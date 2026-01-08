"""
AeroSense System Controller.

This module acts as the central control system for the AeroSense Garden.
It orchestrates hardware interactions, safety logic, and coordinates data logging across all subsystems.
"""

import logging
import time
import threading
from typing import Dict, Optional, Tuple, List

from aerosense.core.logger import Logger
from aerosense.hardware.arduino import Arduino
from aerosense.hardware.camera import Camera
from config import settings

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

        self.camera_lock = threading.Lock()
        self.scan_lock = threading.Lock()

        # State tracking: Keeps Python state in sync with Physical state
        self.state = {
            "lights": False,
            "pump": False,
            "pump_start_time": 0.0,
            "pump_expected_duration": 0.0,
            "last_water_level": 0,
            "last_water_check": 0.0
        }

        self.log.info("System Controller Initialized.")
        self.sync_state()

    def update(self):
        """
        Main logic loop.

        Handles continuous monitoring tasks such as:
        Pump Safety: Ensuring pump does not exceed max runtime.
        Water Level Safety: Ensuring pump does not run dry.
        """
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
                return 
            if current_level >= settings.PUMP_SAFETY_THRESHOLD_MM:
                self.log.warning(f"PUMP ABORT: Water level too low ({current_level}mm).")
                return

            # Update state
            self.state["pump"] = True
            self.state["pump_start_time"] = time.time()
            self.state["pump_expected_duration"] = safe_duration
            
            # Execute command
            self.log.info(f"Starting Pump for {safe_duration}s")
            self.arduino.send(f"PUMP ON {safe_duration * 1000}")
            self.logger.log_pump("ON", safe_duration)

        else:
            # Turn OFF
            self.state["pump"] = False
            self.arduino.send("PUMP OFF")
            self.logger.log_pump("OFF", 0)

    def set_lights(self, state: bool, duration: int = 0) -> None:
        """
        Toggle the grow lights.

        Args:
            state (bool): True for ON, False for OFF.
            duration (int): Duration in seconds (0 for indefinite).
        """
        # Update State
        self.state["lights"] = state
        
        
        # Build command
        cmd_str = "ON" if state else "OFF"
        command = f"LIGHTS {cmd_str}"

        # Hardware logic
        if state and duration > 0:
            command += f" {duration * 1000}"
            
        # Execute command
        if self.arduino.send(command):
            self.logger.log_lights(cmd_str, duration)
        else:
            # Handle errors
            self.log.error("Failed to send LIGHTS command.")

    def stop_all(self, scheduler=None):
        """
        Emergency stop command. Shuts down all actuators immediately.

        Args:
            scheduler (Optional[Scheduler]): If provided, stops automation cycles.
        """
        self.log.warning("Sending Emergency STOP.")
        
        # Kill physical hardware
        self.state["lights"] = False
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
                return vals
            except (ValueError, IndexError):
                # Handle data errors
                self.log.error(f"Malformed temp data: {data}")
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
                return level
            except ValueError:
                # Handle data errors
                self.log.error(f"Malformed distance data: {data}")
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
        if not blocking and self.scan_lock.locked():
            self.log.warning("Skipping Master Task: Previous scan still active (Ghost Thread Prevented).")
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
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
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

        Args:
            count (int): The exact number of images to capture.

        Returns:
            List[str]: A list of the generated filenames.
        """
        with self.camera_lock:
            # Check previous state
            was_lights_on = self.state["lights"]

            # Turn Lights ON (if they were off)
            if not was_lights_on:
                self.log.info("Camera Flash: Toggling lights ON.")
                self.set_lights(True) 
                time.sleep(1.0)

            # Capture images
            try:
                images = self.camera.capture_sequence(count)
            except Exception as e:
                self.log.error(f"Camera Thread Error: {e}")
                images = []

            # Restore environment (Lights Off)
            if not was_lights_on:
                self.log.info("Camera Flash: Restoring lights OFF.")
                self.set_lights(False)

            # Log photos
            if images:
                self.logger.log_camera(images)
            
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

    def check_pi_health(self) -> float:
        """
        Read and log the Raspberry Pi CPU temperature.

        Returns:
            float: CPU temperature in Celsius.
        """
        try:
            # Read data
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp_c = float(f.read()) / 1000.0
                self.logger.log_pi_temp(temp_c)
                return temp_c
        except IOError:
            # Handle data errors
            self.log.error("Could not read Pi thermal zone.")
            return 0.0

    def play_music(self, song_name: str):
        """
        Play a song or note via the Arduino buzzer.
        
        Args:
            song_name (str): Name of song (DAISY, ULTRON) or Note (C4, A5).
        """
        clean_name = song_name.strip().upper()
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
            if self.camera_lock.locked():
                return "BUSY (Capturing)"
            return "IDLE (Ready)"

        # External arduino checks
        fw_target = target
        if target == "ENVIRONMENT": fw_target = "TEMP"
        if target == "WATER_LEVEL": fw_target = "DIST"
        
        # Capture timestamp before sending ping
        request_time = time.time()

        # Send Command
        if not self.arduino.send(f"PING {fw_target}"):
            return "CONNECTION_ERROR"

        # Wait for specific response, ensuring it is fresh
        response = self.arduino.get_latest_data("PONG", min_timestamp=request_time, timeout=1.0)
        return response if response else "TIMEOUT"

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
        elif "OFF" in lights_res:
            self.state["lights"] = False
            
        self.log.info("State Sync Complete.")