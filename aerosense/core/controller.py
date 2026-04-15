"""
AeroSense System Controller.

This module acts as the central control system for the AeroSense Garden.
It orchestrates hardware interactions, safety logic, and coordinates data logging across all subsystems.
"""

import csv
import logging
import random
import shutil
import time
import threading
from datetime import date
from pathlib import Path
from typing import Dict, Optional, Tuple, List

from aerosense.core.logger import Logger
from aerosense.hardware.arduino import Arduino
from aerosense.hardware.camera import Camera
from aerosense.ml.health import HealthClassifier
from aerosense.ml.vision import VisionAnalyzer
from config import settings

# --- Configuration ---
# Valid songs
HAPPY_SONGS = ["DAISY", "FIGHT", "MV1"]
ANGRY_SONGS = ["ULTRON", "FNAF"]
SAD_SONGS = ["SPONGE", "VIOLIN"]
SERIOUS_SONGS = ["SUCCESSION", "TARS", "F1"]
OTHER_SONGS = ["MORNING", "SLEEP", "CURIOSITY", "ALMA"]

SYSTEM_SOUNDS = ["PANIC", "WARNING", "TEST", "GRANTED", "DENIED"]

VALID_SONGS = HAPPY_SONGS + ANGRY_SONGS + SAD_SONGS + SERIOUS_SONGS + OTHER_SONGS + SYSTEM_SOUNDS

SHUFFLE_POOL = HAPPY_SONGS + ANGRY_SONGS + SAD_SONGS + SERIOUS_SONGS + OTHER_SONGS

CATEGORY_POOLS = {
    "HAPPY": HAPPY_SONGS,
    "ANGRY": ANGRY_SONGS,
    "SAD": SAD_SONGS,
    "SERIOUS": SERIOUS_SONGS,
    "OTHER": OTHER_SONGS,
    "SYSTEM": SYSTEM_SOUNDS,
}

# Valid notes
VALID_NOTES = []
_notes = ["C", "CS", "D", "DS", "E", "F", "FS", "G", "GS", "A", "AS", "B"]
for octave in range(3, 8):
    for n in _notes:
        VALID_NOTES.append(f"{n}{octave}")
VALID_NOTES.append("C8")

class Controller:
    """
    High-level controller for the AeroSense system.

    Attributes:
        arduino (Arduino): The serial communication driver.
        camera (Camera): The hardware camera driver.
        logger (Logger): Centralized telemetry logger.
        log (logging.Logger): Dedicated debug logger for control logic.
        state (Dict): Internal dictionary tracking the current state of actuators.
    """

    def __init__(self):
        """
        Initialize the Controller and its subsystems.
        """
        self.log = logging.getLogger("AeroSense.Core.Controller")
        
        self.logger = Logger()
        self.arduino = Arduino()
        self.camera = Camera()
        self.vision = VisionAnalyzer()
        self.health = HealthClassifier()

        self.camera_lock = threading.Lock()
        self.scan_lock = threading.Lock()
        self._scan_thread: Optional[threading.Thread] = None

        # State tracking: Keeps Python state in sync with Physical state
        self.state = {
            "lights": False,
            "lights_start_time": 0.0,
            "lights_expected_duration": 0.0,
            "pump": False,
            "pump_start_time": 0.0,
            "pump_expected_duration": 0.0,
            "last_water_level": 0,
            "last_water_check": 0.0
        }

        # Data cache
        self.data_cache = {
            # Readings
            "temp_reading":      {"value": None, "timestamp": 0},
            "humidity_reading":  {"value": None, "timestamp": 0},
            "water_reading":     {"value": None, "timestamp": 0},
            "pi_health_reading": {
                "value": {"temp": 0, "ram": 0, "disk": 0, "uptime": 0}, 
                "timestamp": 0
            },
            "latest_photo":      {"value": None, "timestamp": 0},
            "vision_result":     {"value": None, "timestamp": 0},
            "health_result":     {"value": None, "timestamp": 0},

            # Pings (Status)
            "ping_env":    {"value": "UNKNOWN", "timestamp": 0},
            "ping_water":  {"value": "UNKNOWN", "timestamp": 0},
            "ping_lights": {"value": "UNKNOWN", "timestamp": 0},
            "ping_pump":   {"value": "UNKNOWN", "timestamp": 0},
            "ping_cam":    {"value": "UNKNOWN", "timestamp": 0},
            "ping_system": {"value": "UNKNOWN", "timestamp": 0},
            "ping_buzzer": {"value": "UNKNOWN", "timestamp": 0}
        }

        # Heartbeat tracking
        self._last_heartbeat_time: float = 0.0
        self._heartbeat_fail_count: int = 0

        # Restore last-known photo/vision from disk so the GUI is not empty on load
        self._hydrate_cache_from_disk()

        # Startup safety: Clear any lingering hardware state from a prior session
        self.arduino.send("STOP")
        self.log.info("Startup Safety: Sent preemptive STOP to hardware.")

        self.log.info("System Controller Initialized.")
        self.sync_state()

    def update(self):
        """
        Main logic loop.

        Handles continuous monitoring tasks such as:
        Pump Safety: Ensuring pump does not exceed max runtime.
        Water Level Safety: Ensuring pump does not run dry.
        """
        # Hardware reboot
        if self.arduino.reboot_detected:
            self.log.warning("Handling Hardware Reboot: Syncing State...")
            self.sync_state()
            self.arduino.reboot_detected = False

        # Pump safety monitor
        if self.state["pump"]:
            now = time.time()
            elapsed = now - self.state["pump_start_time"]
            
            # Turn off water loop
            expected = self.state["pump_expected_duration"]
            if expected > 0 and elapsed > (expected + 0.5):
                self.log.info(f"Pump cycle finished normally ({int(elapsed)}s).")
                self.state["pump"] = False
                self.state["pump_expected_duration"] = 0.0
                return
            
            # Water duration check
            if elapsed > settings.PUMP_MAX_DURATION_SEC:
                self.set_pump(False)
                self.log.warning("Pump exceeded Max Safety Limit (Python Tracker). Forcing Stop.")
                self.play_music("DENIED")
                return

            # Water level check
            if now - self.state["last_water_check"] > settings.PUMP_SAFETY_INTERVAL_SEC:
                level = self.read_water_level(log_data=False)
                self.state["last_water_check"] = now

                # If sensor reads 'Empty', kill pump immediately
                if level and level >= settings.PUMP_SAFETY_THRESHOLD_MM:
                    self.set_pump(False)
                    self.log.critical(f"EMERGENCY STOP: Water level dropped ({level}mm) during cycle!")
                    self.logger.log_alert("Pump aborted mid-cycle: Low Water.")
                    self.play_music("PANIC")

        # Lights safety monitor
        if self.state["lights"] and self.state["lights_start_time"] > 0:
            now = time.time()
            elapsed = now - self.state["lights_start_time"]

            # Timed command completion
            expected = self.state["lights_expected_duration"]
            if expected > 0 and elapsed > (expected + 1.0):
                self.log.info(f"Lights timed cycle finished ({int(elapsed)}s).")
                self.set_lights(False)
                return

            # Max duration hard cap (24h failsafe)
            if elapsed > settings.LIGHTS_MAX_DURATION_SEC:
                self.set_lights(False)
                self.log.warning("Lights exceeded Max Safety Limit. Forcing OFF.")
                self.play_music("DENIED")
                return

        # Arduino heartbeat (every 15 seconds)
        now = time.time()
        if now - self._last_heartbeat_time >= 15.0:
            self._last_heartbeat_time = now

            request_time = time.time()
            if self.arduino.send("HEARTBEAT"):
                response = self.arduino.get_latest_data("HEARTBEAT", min_timestamp=request_time, timeout=0.5)
                if response:
                    self._heartbeat_fail_count = 0
                else:
                    self._heartbeat_fail_count += 1
                    self.log.warning(f"Arduino heartbeat missed ({self._heartbeat_fail_count}/3)")
            else:
                self._heartbeat_fail_count += 1
                self.log.warning(f"Arduino heartbeat send failed ({self._heartbeat_fail_count}/3)")

            if self._heartbeat_fail_count >= 3:
                self.log.critical("Arduino unresponsive after 3 heartbeats. Attempting reconnection.")
                self.arduino.disconnect()
                if self.arduino.connect():
                    self.arduino.start_listener()
                    self._heartbeat_fail_count = 0
                    self.sync_state()
                else:
                    self.log.critical("Arduino reconnection failed.")

    def _hydrate_cache_from_disk(self) -> None:
        """
        Seed the data cache with the most recent photo and vision artifacts on disk
        so the GUI shows last-known state after a restart, instead of empty placeholders.
        """
        # Latest camera photo
        try:
            if settings.IMG_DIR.exists():
                img_files = [p for p in settings.IMG_DIR.iterdir()
                             if p.is_file() and p.suffix.lower() in ('.jpg', '.jpeg', '.png')]
                if img_files:
                    latest = max(img_files, key=lambda p: p.stat().st_mtime)
                    self.data_cache["latest_photo"] = {
                        "value": latest.name,
                        "timestamp": latest.stat().st_mtime,
                    }
        except Exception as e:
            self.log.warning(f"Hydrate: could not scan images dir: {e}")

        # Latest vision result (masked tile + class ratios from CSV)
        try:
            if not settings.VISION_DIR.exists():
                return
            vis_files = [p for p in settings.VISION_DIR.iterdir()
                         if p.is_file() and p.name.endswith('_vision.jpg')]
            if not vis_files:
                return
            latest_vis = max(vis_files, key=lambda p: p.stat().st_mtime)
            source_stem = latest_vis.name[:-len('_vision.jpg')]

            total_px = green_px = 0
            class_pixels: Dict[str, int] = {}
            src_image = ""

            vision_log = self.logger.paths.get("vision")
            if vision_log and vision_log.exists():
                with open(vision_log, 'r', newline='') as f:
                    rows = list(csv.reader(f))
                for row in reversed(rows[1:]):
                    if len(row) < 9:
                        continue
                    if Path(row[1]).stem != source_stem:
                        continue
                    try:
                        total_px = int(row[2])
                        green_px = int(row[3])
                        class_pixels = {
                            "chlorosis": int(row[4]),
                            "necrosis":  int(row[5]),
                            "pest":      int(row[6]),
                            "tip_burn":  int(row[7]),
                            "wilting":   int(row[8]),
                        }
                        src_image = row[1]
                    except ValueError:
                        continue
                    break

            self.data_cache["vision_result"] = {
                "value": {
                    "total_pixels": total_px,
                    "green_pixels": green_px,
                    "class_pixels": class_pixels,
                    "vision_image": latest_vis.name,
                    "model_active": False,
                    "source_image": src_image,
                },
                "timestamp": latest_vis.stat().st_mtime,
            }
        except Exception as e:
            self.log.warning(f"Hydrate: could not restore vision result: {e}")

    def _update_cache(self, key: str, value):
        """
        Updates the internal data cache with a new value and the current timestamp.
        Args:
            key (str): The specific cache key to update (e.g., 'temp_reading', 'ping_pump').
            value (Any): The new data or status string to store.
        """
        if key in self.data_cache:
            self.data_cache[key] = {
                "value": value,
                "timestamp": time.time()
            }

    # --- Actuator Control ---
    def set_pump(self, state: bool, duration: int = 0) -> None:
        """
        Toggle the water pump with safety checks.

        Args:
            state (bool): True for ON, False for OFF.
            duration (int): Desired run time in seconds.
        """
        if state:
            # Enforce max runtime safety cap
            safe_duration = min(duration, settings.PUMP_MAX_DURATION_SEC)
            if safe_duration <= 0:
                safe_duration = settings.PUMP_MAX_DURATION_SEC

            # Check Water Level
            current_level = self.read_water_level(log_data=False)
            if current_level is None:
                self.log.error("PUMP ABORT: Could not read water level sensor.")
                self.play_music("DENIED")
                return 
            if current_level >= settings.PUMP_SAFETY_THRESHOLD_MM:
                self.log.warning(f"PUMP ABORT: Water level too low ({current_level}mm).")
                self.play_music("DENIED")
                return

            # Update state
            self.state["pump"] = True
            self.state["pump_start_time"] = time.time()
            self.state["pump_expected_duration"] = safe_duration
            
            # Execute command
            self.log.info(f"Starting Pump for {safe_duration}s")
            request_time = time.time()
            self.arduino.send(f"PUMP ON {safe_duration * 1000}")
            self.logger.log_pump("ON", safe_duration)

            # Verify command was received by hardware
            ack = self.arduino.get_latest_data("ACK", min_timestamp=request_time, timeout=1.5)
            if ack is None or "PUMP_ON" not in ack:
                self.log.warning(f"Pump ACK not received (got: {ack}). Retrying command.")
                self.arduino.send(f"PUMP ON {safe_duration * 1000}")

        else:
            # Turn OFF
            self.state["pump"] = False
            self.arduino.send("PUMP OFF")
            self.logger.log_pump("OFF", 0)

    def set_lights(self, state: bool, duration: int = 0) -> None:
        """
        Toggle the grow lights with safety tracking.

        Args:
            state (bool): True for ON, False for OFF.
            duration (int): Duration in seconds (0 for indefinite).
        """
        if state:
            # Enforce max duration safety cap on timed commands
            safe_duration = min(duration, settings.LIGHTS_MAX_DURATION_SEC) if duration > 0 else 0

            # Update state
            self.state["lights"] = True
            self.state["lights_start_time"] = time.time()
            self.state["lights_expected_duration"] = float(safe_duration)

            # Build command
            command = "LIGHTS ON"
            if safe_duration > 0:
                command += f" {safe_duration * 1000}"

            # Execute command
            request_time = time.time()
            if self.arduino.send(command):
                self.logger.log_lights("ON", safe_duration)

                # Verify command was received by hardware
                ack = self.arduino.get_latest_data("ACK", min_timestamp=request_time, timeout=1.5)
                if ack is None or "LIGHTS_ON" not in ack:
                    self.log.warning(f"Lights ACK not received (got: {ack}). Retrying command.")
                    self.arduino.send(command)
            else:
                self.log.error("Failed to send LIGHTS command.")
                self.play_music("DENIED")
        else:
            # Update state
            self.state["lights"] = False
            self.state["lights_start_time"] = 0.0
            self.state["lights_expected_duration"] = 0.0

            # Execute command
            if self.arduino.send("LIGHTS OFF"):
                self.logger.log_lights("OFF", 0)
            else:
                self.log.error("Failed to send LIGHTS command.")
                self.play_music("DENIED")

    def set_setting(self, key: str, value: int) -> str:
        """
        Update a runtime system setting with validation.

        Args:
            key (str): The setting name (lights_start, lights_end, pump_duration, pump_interval).
            value (int): The new integer value.

        Returns:
            str: Success or error message.
        """
        if not isinstance(value, int):
            return "Error: Value must be an integer."

        if key == "lights_start":
            if value < 0 or value > 23:
                return "Error: Lights start hour must be 0-23."
            if value >= settings.LIGHTS_END_HOUR:
                return f"Error: Start hour ({value}) must be before end hour ({settings.LIGHTS_END_HOUR})."
            old = settings.LIGHTS_START_HOUR
            settings.LIGHTS_START_HOUR = value
            self.log.info(f"Setting LIGHTS_START_HOUR changed: {old} -> {value}")
            return f"Lights start hour set to {value}:00 (was {old}:00)."

        elif key == "lights_end":
            if value < 0 or value > 23:
                return "Error: Lights end hour must be 0-23."
            if value <= settings.LIGHTS_START_HOUR:
                return f"Error: End hour ({value}) must be after start hour ({settings.LIGHTS_START_HOUR})."
            old = settings.LIGHTS_END_HOUR
            settings.LIGHTS_END_HOUR = value
            self.log.info(f"Setting LIGHTS_END_HOUR changed: {old} -> {value}")
            return f"Lights end hour set to {value}:00 (was {old}:00)."

        elif key == "pump_duration":
            if value < 1 or value > settings.PUMP_MAX_DURATION_SEC:
                return f"Error: Pump duration must be 1-{settings.PUMP_MAX_DURATION_SEC}s."
            old = settings.PUMP_DURATION_SEC
            settings.PUMP_DURATION_SEC = value
            self.log.info(f"Setting PUMP_DURATION_SEC changed: {old} -> {value}")
            return f"Pump duration set to {value}s (was {old}s)."

        elif key == "pump_interval":
            if value < 1 or value > 1440:
                return "Error: Pump interval must be 1-1440 minutes."
            old = settings.PUMP_INTERVAL_MINS
            settings.PUMP_INTERVAL_MINS = value
            self.log.info(f"Setting PUMP_INTERVAL_MINS changed: {old} -> {value}")
            return f"Pump interval set to {value}min (was {old}min)."

        else:
            return f"Error: Unknown setting '{key}'."

    def stop_all(self, scheduler=None):
        """
        Emergency stop command. Shuts down all actuators immediately.

        Args:
            scheduler (Optional[Scheduler]): If provided, stops automation cycles.
        """
        self.log.warning("Sending Emergency STOP.")
        
        # Kill physical hardware
        self.state["lights"] = False
        self.state["lights_start_time"] = 0.0
        self.state["lights_expected_duration"] = 0.0
        self.state["pump"] = False

        self.arduino.send("STOP")

        self.logger.log_pump("OFF")
        self.logger.log_lights("OFF")
        self.logger.log_music("STOP")
        
        # Kill automation logic
        if scheduler:
            scheduler.stop_all_cycles()

    # --- Sensor Operations ---
    def _read_sensor_raw(self, trigger_cmd: str, data_tag: str, timeout: float = 2.0) -> Optional[str]:
        """
        Generic wrapper to send a command and fetch the raw response string.

        Args:
            trigger_cmd (str): The serial command to send to the Arduino.
            data_tag (str): The data prefix to listen for in the response.
            timeout (float): Max time to wait for a response in seconds.

        Returns:
            Optional[str]: The raw data string from the Arduino, or None on timeout.
        """
        request_time = time.time()

        self.arduino.send(trigger_cmd)
        
        data = self.arduino.get_latest_data(data_tag, min_timestamp=request_time, timeout=timeout)
        if not data:
            self.log.error(f"Timeout waiting for {trigger_cmd}")
        return data
    
    def read_environment(self) -> Optional[Tuple[float, float]]:
        """
        Read temperature and humidity from the sensor.

        Returns:
            Optional[Tuple[float, float]]: (Temp_F, Humidity_RH) or None on failure.
        """
        # Read data
        data = self._read_sensor_raw("READ_TEMP", "DATA_TEMP", 3.0)
        
        if data:
            try:
                parts = data.split(",")
                vals = (float(parts[0]), float(parts[1]))
                self.logger.log_environment(*vals)

                # Update Cache
                self._update_cache("temp_reading", vals[0])
                self._update_cache("humidity_reading", vals[1])

                return vals
            except (ValueError, IndexError):
                # Handle data errors
                self.log.error(f"Malformed temp data: {data}")
                self.play_music("DENIED")
        return None

    def read_water_level(self, log_data: bool = True) -> Optional[int]:
        """
        Read the water level.

        Args:
            log_data (bool): Whether to save this reading to the CSV log.

        Returns:
            Optional[int]: Distance in mm (larger number = lower water), or None.
        """
        # Read data
        data = self._read_sensor_raw("READ_DISTANCE", "DATA_DISTANCE", 2.0)
        
        if data:
            try:
                level = int(data)
                if log_data: 
                    self.logger.log_water(level)

                    # Update Cache
                    self._update_cache("water_reading", level)

                return level
            except ValueError:
                # Handle data errors
                self.log.error(f"Malformed distance data: {data}")
                self.play_music("DENIED")
        return None

    def run_master_task(self, blocking: bool = True):
        """
        Runs a comprehensive data sweep (Env + Water + Camera).
        Logs to master_log.csv if all sensors succeed.
        
        Args:
            blocking (bool): True for CLI (wait for result), False for Scheduler (background).

        Returns:
            Tuple: (env_data, water_level) if blocking=True, else (None, None)
        """
        # Thread Safety: Prevent overlapping scans
        if not blocking:
            if self._scan_thread and self._scan_thread.is_alive():
                self.log.warning("Skipping Master Task: Previous background scan still active.")
                self.play_music("DENIED")
                return None, None
            
            if self.scan_lock.locked():
                 self.log.warning("Skipping Master Task: Hardware locked by user command.")
                 self.play_music("DENIED")
                 return None, None

        # Define the worker logic
        def _worker():
            with self.scan_lock:
                # Gather sensor data immediately
                env = self.read_environment() 
                water = self.read_water_level()

                images = self._run_capture_sequence(settings.CAM_BURST_COUNT)
                
                # Log to Master only if everything succeeded
                if env and water and images:
                     self.logger.log_master(env[0], env[1], water, images)

                return env, water

        # Execute
        if blocking:
            return _worker()
        else:
            self._scan_thread = threading.Thread(target=_worker, daemon=True)
            self._scan_thread.start()
            return None, None

    def capture_smart_image(self, count: int = None, blocking: bool = True) -> List[str]:
        """
        Capture a visual log (Burst of N images).
        
        Args:
            count (int, optional): 
                The number of images to capture. 
                If None, defaults to the system configuration (CAM_BURST_COUNT).
            blocking (bool): 
                If True, waits for images to save and returns the list of files.
                If False, runs in background and returns an empty list immediately.
                
        Returns:
            List[str]: Filenames of captured images (only if blocking=True).
        """
        # Set default if not provided
        if count is None:
            count = settings.CAM_BURST_COUNT
        
        # If we are already taking photos skip this request
        if self.camera_lock.locked():
            self.log.warning("Capture skipped: Camera is already busy.")
            self.play_music("DENIED")
            return []

        if blocking:
            # Run normally in the main thread
            return self._run_capture_sequence(count)
        else:
            # Spin up a background thread
            t = threading.Thread(target=self._run_capture_sequence, args=(count,), daemon=True)
            t.start()
            return []
        
    def _run_capture_sequence(self, count: int) -> List[str]:
        """
        Internal Logic: Executes camera sequence with thread locking.
        Ensures lights are ON during capture and restores them afterwards.
        Pauses any active live stream and resumes it after capture.

        Args:
            count (int): The exact number of images to capture.

        Returns:
            List[str]: A list of the generated filenames.
        """
        with self.camera_lock:
            # Pause live stream if active (only one process can use camera at a time)
            was_streaming = self.camera.is_streaming
            if was_streaming:
                self.log.info("Pausing live stream for capture.")
                self.camera.stop_stream()
                time.sleep(0.5)

            # Check previous state
            was_lights_on = self.state["lights"]

            # Turn Lights ON (if they were off)
            if not was_lights_on:
                self.log.info("Camera Flash: Toggling lights ON.")
                self.set_lights(True)
                time.sleep(2.0)

            # Capture images
            try:
                images = self.camera.capture_sequence(count)
            except Exception as e:
                self.log.error(f"Camera Thread Error: {e}")
                self.play_music("DENIED")
                images = []

            # Restore environment (Lights Off)
            if not was_lights_on:
                self.log.info("Camera Flash: Restoring lights OFF.")
                self.set_lights(False)

            # Log photos
            if images:
                self.logger.log_camera(images)

                # Update cache
                self._update_cache("latest_photo", images[-1])

            # Resume live stream if it was active before capture
            if was_streaming:
                self.log.info("Resuming live stream after capture.")
                self.camera.start_stream()

            return images
    
    def run_live_camera(self, duration: int) -> None:
        """
        Turn on the camera viewfinder via HDMI for manual adjustments.

        Args:
            duration (int): Duration in seconds. 0 for indefinite execution.
        """
        should_toggle_lights = (duration > 0)
        was_lights_on = self.state["lights"]

        # Setup environment
        if should_toggle_lights and not was_lights_on:
            self.log.info("Live Camera: Turning lights ON for visibility.")
            self.set_lights(True)
            time.sleep(0.5)

        # Execute hardware driver
        self.camera.start_preview(duration)

        # Restore environment
        if should_toggle_lights and not was_lights_on:
            self.set_lights(False)
            self.log.info("Live Camera: Restoring lights to OFF.")

    def start_live_stream(self) -> bool:
        """
        Start the MJPEG live stream for the web interface.

        Returns:
            bool: True if stream started, False if camera is busy.
        """
        if self.camera_lock.locked():
            self.log.warning("Cannot start stream: Camera is busy with a capture.")
            return False
        return self.camera.start_stream()

    def stop_live_stream(self):
        """Stop the MJPEG live stream."""
        self.camera.stop_stream()

    def check_pi_health(self) -> Dict[str, float]:
        """
        Perform a comprehensive system health check.

        Returns:
            Dict[str, float]: A dictionary containing 'temp', 'ram', 'disk', and 'uptime'.
        """
        stats = {
            "temp": 0.0,
            "ram": 0.0,
            "disk": 0.0,
            "uptime": 0.0
        }

        # CPU temperature
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                stats["temp"] = round(float(f.read()) / 1000.0, 1)
        except Exception:
            self.log.error("Failed to read CPU Temp")

        # RAM usage
        try:
            with open("/proc/meminfo", "r") as f:
                mem = {}
                for line in f:
                    parts = line.split()
                    mem[parts[0].strip(":")] = int(parts[1])
            
            total = mem.get("MemTotal", 1)
            avail = mem.get("MemAvailable", 0)
            stats["ram"] = round(100 * (1 - (avail / total)), 1)
        except Exception:
            self.log.error("Failed to read RAM Usage")

        # Disk usage
        try:
            _, _, free = shutil.disk_usage(settings.DATA_DIR)
            stats["disk"] = round(free / (2**30), 2)
            
            if stats["disk"] < 1.0:
                 self.log.critical("LOW DISK SPACE WARNING")
                 self.play_music("PANIC")
        except Exception:
            self.log.error("Failed to read Disk Usage")

        # Uptime
        try:
            with open("/proc/uptime", "r") as f:
                seconds = float(f.read().split()[0])
                stats["uptime"] = round(seconds / 3600, 1)
        except Exception:
            self.log.error("Failed to read Uptime")

        # Log and Cache
        self.logger.log_pi_stats(stats["temp"], stats["ram"], stats["disk"], stats["uptime"])
        self._update_cache("pi_health_reading", stats)
        
        return stats

    def play_music(self, song_name: str):
        """
        Play a song or note via the Arduino buzzer.
        
        Args:
            song_name (str): Name of song (DAISY, ULTRON) or Note (C4, A5).
        """
        clean_name = song_name.strip().upper()

        if clean_name.startswith("RANDOM_"):
            category = clean_name[7:]
            pool = CATEGORY_POOLS.get(category, [])
            if not pool:
                self.log.warning(f"Random category '{category}' not found or empty!")
                return
            clean_name = random.choice(pool)
            self.log.info(f"Randomly selected {category} song: {clean_name}")
        elif clean_name == "RANDOM":
            if not SHUFFLE_POOL:
                self.log.warning("Random shuffle requested, but SHUFFLE_POOL is empty!")
                return
            clean_name = random.choice(SHUFFLE_POOL)
            self.log.info(f"Randomly selected song: {clean_name}")

        self.log.info(f"Music Request: {clean_name}")
        
        if self.arduino.send(f"MUSIC PLAY {clean_name}"):
            self.logger.log_music(clean_name)
    
    def stop_music(self):
        """Stop audio playback."""
        self.arduino.send("MUSIC STOP")
        self.logger.log_music("STOP")

    # --- System Operations ---
    def ping_component(self, target: str) -> str:
        """
        Send a specific PING to hardware or check internal Python state.
        
        Args:
            target (str): PUMP, LIGHTS, TEMP, DIST, MUSIC, CAMERA.
            
        Returns:
            str: The status string (e.g., "PUMP_ON", "DIST_OK", "IDLE").
        """
        target = target.upper()
        
        # Internal python checks
        if target == "CAMERA":
            status = "BUSY (Capturing)" if self.camera_lock.locked() else "IDLE (Ready)"
            self._update_cache("ping_cam", status)
            return status
        
        fw_target = target
        cache_key = None
        
        if target == "ENVIRONMENT": 
            fw_target = "TEMP"
            cache_key = "ping_env"
        elif target == "WATER_LEVEL": 
            fw_target = "DIST"
            cache_key = "ping_water"
        elif target == "PUMP":
            cache_key = "ping_pump"
        elif target == "LIGHTS":
            cache_key = "ping_lights"
        elif target == "MUSIC":
            cache_key = "ping_buzzer"
        elif target == "SYSTEM":
            fw_target = "SYSTEM"
            cache_key = "ping_system"
        
        # Capture timestamp before sending ping
        request_time = time.time()

        # Send Command
        if not self.arduino.send(f"PING {fw_target}"):
            res = "CONNECTION_ERROR"
            if cache_key: self._update_cache(cache_key, res)
            return res

        # Wait for target-specific response to avoid cross-contamination during PING ALL
        response = self.arduino.get_latest_data(f"PONG_{fw_target}", min_timestamp=request_time, timeout=1.0)
        
        final_result = response if response else "TIMEOUT"

        # Update cache
        if cache_key:
            self._update_cache(cache_key, final_result)
            
        return final_result

    def run_full_diagnostic(self):
        """
        Perform a full sensor sweep and system health check.
        
        Returns:
            Dict: Contains 'env', 'water', and 'pi' data.
        """
        self.log.info("Starting System Diagnostic Sweep...")
        
        env, water = self.run_master_task(blocking=True)
        pi_temp = self.check_pi_health()
        
        self.log.info("Diagnostic Complete.")

        return {
            "env": env,
            "water": water,
            "pi": pi_temp
        }

    def split_latest_image(self) -> List[str]:
        """
        Capture a fresh photo, then split it into a 3x2 grid of 6 tiles
        and save the tiles to the tiles directory.

        Returns:
            List[str]: A list of 6 generated tile filenames, or an empty list on failure.
        """
        import cv2

        # Capture a fresh image first
        images = self.capture_smart_image(blocking=True)
        if not images:
            self.log.error("SPLIT CAM: Capture failed.")
            self.play_music("DENIED")
            return []

        camera_log_path = self.logger.paths["camera"]
        tiles_dir: Path = settings.TILES_DIR

        # Read camera log for latest image
        if not camera_log_path.exists():
            self.log.error("SPLIT CAM: Camera log does not exist. No images have been captured.")
            return []

        latest_image = None
        try:
            with open(camera_log_path, 'r', newline='') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if header is None:
                    self.log.error("SPLIT CAM: Camera log is empty.")
                    return []

                last_row = None
                for row in reader:
                    last_row = row

                if last_row is None:
                    self.log.error("SPLIT CAM: Camera log has no entries.")
                    return []

                # Validate row has expected columns
                if len(last_row) < 2:
                    self.log.error("SPLIT CAM: Most recent camera log row is malformed.")
                    return []

                # Image_Paths column may contain multiple filenames separated by ";"
                image_paths_str = last_row[1].strip()
                if not image_paths_str:
                    self.log.error("SPLIT CAM: Most recent camera log entry has no image paths.")
                    return []

                # Take the last image from the entry
                image_names = [name.strip() for name in image_paths_str.split(";") if name.strip()]
                if not image_names:
                    self.log.error("SPLIT CAM: Most recent camera log entry has no valid image paths.")
                    return []
                latest_image = image_names[-1]

        except Exception as e:
            self.log.error(f"SPLIT CAM: Failed to read camera log: {e}")
            return []

        # Verify source image exists
        source_path = settings.IMG_DIR / latest_image
        if not source_path.exists():
            self.log.error(f"SPLIT CAM: Source image not found: {source_path}")
            return []

        # Load and split the image into a 3x2 grid
        try:
            img = cv2.imread(str(source_path))
            if img is None:
                self.log.error(f"SPLIT CAM: Failed to decode image: {source_path}")
                return []

            height, width = img.shape[:2]
            tile_w = width // 3
            tile_h = height // 2

            stem = source_path.stem
            ext = source_path.suffix

            tile_filenames = []
            tile_index = 1

            # 2 rows, 3 columns - left to right, top to bottom
            for row in range(2):
                for col in range(3):
                    x1 = col * tile_w
                    y1 = row * tile_h
                    # Use full remaining pixels on last column/row to avoid losing edge pixels
                    x2 = width if col == 2 else (col + 1) * tile_w
                    y2 = height if row == 1 else (row + 1) * tile_h

                    tile = img[y1:y2, x1:x2]
                    tile_name = f"{stem}_{tile_index}{ext}"
                    tile_path = tiles_dir / tile_name

                    success = cv2.imwrite(str(tile_path), tile)
                    if not success:
                        self.log.error(f"SPLIT CAM: Failed to write tile: {tile_name}")
                        return []
                    tile_filenames.append(tile_name)
                    tile_index += 1

            # Log the split operation
            self.logger.log_tiles(tile_filenames)
            self.log.info(f"SPLIT CAM: Successfully split '{latest_image}' into {len(tile_filenames)} tiles.")

            return tile_filenames

        except Exception as e:
            self.log.error(f"SPLIT CAM: Image processing failed: {e}")
            return []

    def run_vision_analysis(self, silent: bool = False) -> Optional[Dict]:
        """
        Run the full vision analysis pipeline: capture, tile, analyze, log.

        Args:
            silent (bool): If True, suppress audio feedback (used when called from health pipeline).

        Returns:
            Optional[Dict]: Results dict with pixel counts and vision tile paths, or None on failure.
        """
        # Capture and split into tiles
        tile_names = self.split_latest_image()
        if not tile_names:
            self.log.error("Vision: Capture/tiling failed.")
            return None

        # Get source image name from cache (set by capture inside split)
        source_image = self.data_cache["latest_photo"]["value"] or "unknown"

        # Run vision analysis on all tiles
        tile_paths = [str(settings.TILES_DIR / name) for name in tile_names]
        source_stem = Path(source_image).stem
        result = self.vision.analyze_all_tiles(tile_paths, settings.VISION_DIR, source_stem)
        if result is None:
            self.log.error("Vision: Analysis failed on all tiles.")
            if not silent:
                self.play_music("DENIED")
            return None

        # Log results
        self.logger.log_vision(source_image, result["total_pixels"],
                               result["green_pixels"], result["class_pixels"])

        # Cache for GUI
        self._update_cache("vision_result", {
            "total_pixels": result["total_pixels"],
            "green_pixels": result["green_pixels"],
            "class_pixels": result["class_pixels"],
            "vision_image": result["vision_image"],
            "model_active": result["model_active"],
            "source_image": source_image
        })

        if not silent:
            if result.get("model_active"):
                print(">> [MODEL ACTIVE] RoboFlow model loaded and running.")
            else:
                print(">> [MODEL INACTIVE] No RoboFlow model — class pixels will be 0.")
            print(f"\n--- VISION ANALYSIS ---")
            print(f">> Total Pixels:  {result['total_pixels']}")
            print(f">> Green Pixels:  {result['green_pixels']}")
            for cls in settings.VISION_CLASSES:
                print(f">> {cls.capitalize():12s}: {result['class_pixels'].get(cls, 0)} px")
            print("------------------------")
            self.play_music("GRANTED")
        return result

    def run_plant_health(self) -> Optional[Dict]:
        """
        Run the full plant health classification pipeline.

        Steps: vision capture → environment read → feature computation → XGBoost prediction → log.
        Gracefully handles missing model by logging features with prediction="NO_MODEL".
        Acquires scan_lock to prevent concurrent hardware access with run_master_task.

        Returns:
            Optional[Dict]: Result with 'prediction' and 'features', or None on pipeline failure.
        """
        if self.scan_lock.locked():
            self.log.warning("Plant Health: Skipped — hardware locked by another task.")
            self.play_music("DENIED")
            return None

        with self.scan_lock:
            self.log.info("Plant Health: Starting analysis pipeline...")

            # Run vision pipeline (capture + tile + inference)
            vision_result = self.run_vision_analysis(silent=True)
            if not vision_result:
                self.log.error("Plant Health: Vision pipeline failed.")
                return None

            # Read environment sensors (fresh temp/humidity)
            env_data = self.read_environment()
            if not env_data:
                self.log.error("Plant Health: Environment read failed.")
                return None

            # Compute features (works even without model)
            features = self.health.compute_features(vision_result, env_data, self.logger.log_dir)
            if not features:
                self.log.error("Plant Health: Feature computation failed.")
                return None

            # Predict (may return None if model missing)
            pred_result = self.health.predict(features)
            if not pred_result:
                prediction = "NO_MODEL"
                confidence = 0.0
                self.logger.log_health(features, prediction, confidence)
                result = {"prediction": prediction, "confidence": confidence, "features": features}
                self._update_cache("health_result", result)
                self.play_music("DENIED")
                print("\n--- PLANT HEALTH ---")
                print(">> [NO MODEL] Health model not loaded.")
                print(">> Run scripts/train_health.py on your PC to generate models/health_model.pkl")
                print(">> Features were still computed and logged to health_log.csv.")
                self._print_health_features(features)
                print("--------------------")
                return result

            prediction, confidence = pred_result

            # Log
            self.logger.log_health(features, prediction, confidence)

            # Cache and return
            result = {"prediction": prediction, "confidence": confidence, "features": features}
            self._update_cache("health_result", result)
            self.play_music("GRANTED")
            print(f"\n--- PLANT HEALTH ---")
            print(f">> Diagnosis: {prediction} ({confidence:.1f}%)")
            self._print_health_features(features)
            print("--------------------")
            return result

    def _print_health_features(self, features: Dict[str, float]) -> None:
        """Print formatted feature values for plant health analysis."""
        print("\n   Features:")
        for k, v in features.items():
            label = k.replace('_', ' ').title()
            print(f"   {label:20s}: {v:.4f}")

    def get_countdown_message(self) -> str:
        """Returns the appropriate countdown message based on today's date."""
        today = date.today()
        delta = (settings.COUNTDOWN_TARGET_DATE - today).days
        if delta > 0:
            return settings.COUNTDOWN_MSG_BEFORE.format(days=delta)
        elif delta == 0:
            return settings.COUNTDOWN_MSG_TODAY
        else:
            return settings.COUNTDOWN_MSG_AFTER

    def sync_state(self):
        """
        Force Python state to match physical Hardware state.
        Resolves 'Split Brain' issues where UI says ON but Pump is OFF.
        """
        self.log.info("Syncing state with Hardware...")
        
        # Sync pump
        pump_res = self.ping_component("PUMP")
        
        if "ON" in pump_res:
            if not self.state["pump"]:
                self.log.warning("State Mismatch Found: Pump was ON, Python thought OFF. Correcting.")
            self.state["pump"] = True
            
        elif "OFF" in pump_res:
            if self.state["pump"]:
                self.log.warning("State Mismatch Found: Pump was OFF, Python thought ON. Correcting.")
            self.state["pump"] = False
            self.state["pump_start_time"] = 0
            self.state["pump_expected_duration"] = 0.0

        # Sync lights
        lights_res = self.ping_component("LIGHTS")

        if "ON" in lights_res:
            self.state["lights"] = True
            if self.state["lights_start_time"] == 0:
                self.state["lights_start_time"] = time.time()
        elif "OFF" in lights_res:
            self.state["lights"] = False
            self.state["lights_start_time"] = 0.0
            self.state["lights_expected_duration"] = 0.0
            
        self.log.info("State Sync Complete.")
        