"""
AeroSense Scheduler.

This module acts as the automation brain of the system. 
It checks the current time against defined schedules and instructs the Controller to actuate hardware or trigger sensor logging tasks.
"""

from datetime import datetime
import logging
import time

from aerosense.core.controller import Controller
from config import settings

# --- Configuration ---
BIRTHDAYS = [
    (1, 1, "MOSS"),
    (2, 13, "The Twins"),
    (3, 7, "Jason"),
    (3, 22, "Josie"),
    (11, 13, "David"),
    (12, 20, "Gabe")
]

class Scheduler:
    """
    Manages automation cycles for lights, pumps, and sensors.

    Attributes:
        controller (Controller): Reference to the hardware controller.
        cycles (dict): Stores which automation cycles are ENABLED/DISABLED.
        last_pump_min (int): Tracks the minute the pump last ran (to prevent double triggering).
        last_sensor_min (int): Tracks the minute sensors were last logged.
    """

    def __init__(self, controller: Controller):
        """
        Initialize the Scheduler.

        Args:
            controller (Controller): The main system controller instance used to execute hardware commands.
        """
        self.log = logging.getLogger("AeroSense.Core.Scheduler")
        self.controller = controller
        
        # Automation state: defaults to False on startup
        self.cycles = {
            # Hardware Actuators
            "lights": False,
            "pump": False,
            
            # Sensor Logging
            "environment": False,
            "water_level": False,
            "camera": False,
            "pi_health": False
        }

        # Manual overrides
        self.manual_override_off = False
        self.manual_override_on = False

        # Interval tracking
        self.last_pump_min = -1
        self.last_sensor_min = -1

        # State tracking
        self.pump_warning_active = False
        self.pump_start_deadline = 0

        self.log.info("Scheduler Initialized. All cycles standing by.")

    def set_cycle(self, component: str, state: bool):
        """
        Enable or Disable a specific automation cycle.
        Supports "Macros" to toggle groups of components at once.

        Args:
            component (str): The name of the cycle (e.g., 'lights') or macro ('system').
            state (bool): True to Enable, False to Disable.
        """
        target = component.lower()
        
        # Define groups using sets of keys
        groups = {
            "hardware": ["lights", "pump"],
            "sensors": ["environment", "water_level", "camera", "pi_health"],
            # "system" is just the union of the two above
            "system": ["lights", "pump", "environment", "water_level", "camera", "pi_health"]
        }

        if target in groups:
            # Update all keys in the group at once
            for key in groups[target]:
                self.cycles[key] = state
            self.log.info(f"Macro: {target.upper()} cycles set to {state}")

        elif target in self.cycles:
            # Update individual component
            self.cycles[target] = state
            self.log.info(f"Cycle '{target}' set to {state}")
            
        else:
            self.log.warning(f"Unknown cycle component: {target}")

        # Turn off hardware if cycle disabled
        if state is False:
            # Pump
            if target in ["pump", "hardware", "system"]:
                if self.controller.state["pump"]:
                     self.log.info(f"Cycle '{target}' Disabled: Turning Pump OFF immediately.")
                self.controller.set_pump(False)
                self.pump_warning_active = False

            # Lights
            if target in ["lights", "hardware", "system"]:
                if self.controller.state["lights"]:
                     self.log.info(f"Cycle '{target}' Disabled: Turning Lights OFF immediately.")
                self.controller.set_lights(False)

    def stop_all_cycles(self):
        """
        Immediately disable all automation cycles.
        Used during emergency stops or shutdown.
        """
        for key in self.cycles:
            self.cycles[key] = False
        self.pump_warning_active = False
        self.log.warning("Scheduler: All cycles DISABLED.")

    def register_manual_light_change(self, state: bool):
        """
        Registers a manual intervention to temporarily override the automation schedule.

        Args:
            state (bool): The new state set by the user (True=ON, False=OFF).
        """
        now = datetime.now()
        start = settings.LIGHTS_START_HOUR
        end = settings.LIGHTS_END_HOUR
        
        # Check if within the active window
        is_active_window = start <= now.hour < end

        if state is True:
            # User turned ON
            self.manual_override_off = False
            if not is_active_window:
                self.manual_override_on = True
                self.log.info("Manual Override: Keeping lights ON until morning.")

        else:
            # User turned OFF
            self.manual_override_on = False
            if is_active_window:
                self.manual_override_off = True
                self.log.info("Manual Override: Keeping lights OFF until evening.")

    def reset_overrides(self):
        """
        Clears all manual overrides. 
        The Scheduler will immediately enforce the programmed schedule on the next update.
        """
        self.manual_override_off = False
        self.manual_override_on = False
        self.log.info("Manual Overrides Cleared. Resuming strict schedule.")

    def get_status(self) -> str:
        """
        Retrieve a summary of the current automation state.

        Returns:
            str: A formatted string listing all cycles and their current ON/OFF status.
        """
        return ", ".join([f"{k.capitalize()}:{'ON' if v else 'OFF'}" for k, v in self.cycles.items()])

    def update(self):
        """
        Main tick function. Checks the current time and executes enabled cycles.
        Should be called continuously from the main loop.
        """
        now = datetime.now()
        current_hour = now.hour
        current_minute = now.minute

        music_played_this_cycle = False

        # --- Lights Schedule ---
        if self.cycles["lights"]:
            start = settings.LIGHTS_START_HOUR
            end = settings.LIGHTS_END_HOUR
            
            # Reset flags
            if current_hour == start:
                self.manual_override_on = False
            if current_hour == end:
                self.manual_override_off = False

            # Check if we are inside the active window and light state
            should_be_on = start <= current_hour < end
            is_currently_on = self.controller.state["lights"]

            # Apply lights logic
            if should_be_on:
                # Turn on lights
                if not is_currently_on and not self.manual_override_off:
                    self.log.info(f"Schedule: Window active. Turning Lights ON.")
                    self.controller.set_lights(True)

                    # Determine Song
                    song_to_play = "MORNING"
                    # Check for birthdays
                    for month, day, name in BIRTHDAYS:
                        if now.month == month and now.day == day:
                            self.log.info(f"Schedule: Special Date detected. Happy Birthday to {name}!")
                            song_to_play = "CURIOSITY"
                            break
                    
                    self.controller.play_music(song_to_play)
                    music_played_this_cycle = True
            
            else:
                # Turn off lights
                if is_currently_on and not self.manual_override_on:
                    if not self.controller.camera_lock.locked():
                        self.log.info(f"Schedule: Window ended. Turning Lights OFF.")
                        self.controller.set_lights(False)
                        self.controller.play_music("SLEEP")
                        music_played_this_cycle = True

        # --- Pump Schedule ---
        if self.cycles["pump"]:
            
            # Trigger the sequence
            if (current_minute % settings.PUMP_INTERVAL_MINS == 0) and (current_minute != self.last_pump_min):
                
                if not self.controller.state["pump"] and not self.pump_warning_active:
                    
                    wait_duration = 8.0
                    
                    # If music already played this tick use that as the warning
                    if music_played_this_cycle:
                         self.log.info("Schedule: Music Syncup detected. Using Lights music as Pump Warning (15s).")
                         wait_duration = 15.0
                    else:
                         self.log.info(f"Schedule: Pump Cycle Pending. Playing Warning (8s).")
                         self.controller.play_music("WARNING")
                    
                    # Set flag and deadline
                    self.pump_warning_active = True
                    self.pump_start_deadline = time.time() + wait_duration
                    
                    self.last_pump_min = current_minute

            # Execute the action
            if self.pump_warning_active:
                if time.time() >= self.pump_start_deadline:
                    self.log.info("Schedule: Warning complete. Activating Pump.")
                    
                    self.controller.set_pump(True, settings.PUMP_DURATION_SEC)
                    
                    # Reset flag
                    self.pump_warning_active = False

        # --- Sensor Logging ---
        if (current_minute % settings.SENSOR_INTERVAL_MINS == 0) and (current_minute != self.last_sensor_min):
            
            self.log.info(f"Schedule: Sensor Interval Reached (Minute : {current_minute:02d})")
            
            # If all main sensors are enabled, run the synchronized "Master Task"
            run_master = (self.cycles["environment"] and 
                          self.cycles["water_level"] and 
                          self.cycles["camera"])

            if run_master:
                # Run the consolidated task in the background
                self.controller.run_master_task(blocking=False)
                
                # Pi Health is not part of the master row, so check it separately
                if self.cycles["pi_health"]:
                    self.controller.check_pi_health()

            else:
                # Run tasks individually if master cycle is broken
                if self.cycles["environment"]:
                    self.controller.read_environment()
                    
                if self.cycles["water_level"]:
                    self.controller.read_water_level()
                    
                if self.cycles["pi_health"]:
                    self.controller.check_pi_health()

                if self.cycles["camera"]:
                    self.controller.capture_smart_image(blocking=False)

            # Prevent this block from running again this minute
            self.last_sensor_min = current_minute