"""
AeroSense Command Line Interface.

This module acts as the user interface layer for the system. 
It processes input from the console, routes commands to the appropriate system logic, and provides real-time feedback to the operator.
"""

import logging
import sys
import threading
from typing import List

from aerosense.core.controller import Controller
from aerosense.core.scheduler import Scheduler

# --- Configuration ---
# Multi-Word sanitization
MULTI_WORD_TOKENS = {
    "WATER PUMP": "PUMP",

    "GROW LIGHTS": "LIGHTS",

    "WATER LEVEL": "WATER_LEVEL",

    "LIVE CAMERA": "LIVE_CAMERA",
    "CAMERA LIVE": "LIVE_CAMERA",

    "PI HEALTH": "PI_HEALTH",
}

# Component normalization
COMPONENT_ALIASES = {
    # System Groups
    "SYS": "SYSTEM",
    "ALL": "SYSTEM",

    "HW": "HARDWARE",
    "DEVICE": "HARDWARE",
    "DEVICES": "HARDWARE",

    "SENSOR": "SENSORS",
    
    # Actuators
    "PUMPS": "PUMP",

    "LIGHT": "LIGHTS",
    "LAMP": "LIGHTS",
    
    # Sensors
    "TEMP": "ENVIRONMENT",
    "TEMPERATURE": "ENVIRONMENT",
    "HUM": "ENVIRONMENT",
    "HUMIDITY": "ENVIRONMENT",
    "ENV": "ENVIRONMENT",
    
    "WATER": "WATER_LEVEL",
    "LEVEL": "WATER_LEVEL",
    "DIST": "WATER_LEVEL",
    "DISTANCE": "WATER_LEVEL",
    
    "CAM": "CAMERA",
    "PIC": "CAMERA",
    "PHOTO": "CAMERA",
    
    "CPU": "PI_HEALTH",
    "PI": "PI_HEALTH",
    "HEALTH": "PI_HEALTH",

    #System Commands
    "COMMANDS": "HELP",
    "COMMAND": "HELP",

    "EXIT": "QUIT"
}


class CLI:
    """
    Handles user input and system feedback via the terminal.

    Attributes:
        controller (Controller): Reference to the main system controller.
        scheduler (Scheduler): Reference to the automation scheduler.
        running (bool): Flag to keep the background input listener alive.
        log (logging.Logger): Dedicated logger for interface events.
    """

    def __init__(self, controller: Controller, scheduler: Scheduler):
        """
        Initialize the CLI.

        Args:
            controller (Controller): The active system controller instance.
            scheduler (Scheduler): The active system scheduler instance.
        """
        self.controller = controller
        self.scheduler = scheduler
        self.running = True
        self.log = logging.getLogger("AeroSense.Interface.CLI")

    # --- COMMAND INTERPRETERS ---
    def start(self):
        """
        Start the input listener in a separate background thread.
        """
        input_thread = threading.Thread(target=self._input_loop, daemon=True)
        input_thread.start()
        print("\n[CLI] Ready. Type 'HELP' for commands.\n")

    def _input_loop(self):
        """
        Continuous loop waiting for user input from stdin.
        """
        while self.running:
            try:
                # Blocking read
                user_input = sys.stdin.readline()
                if not user_input:
                    break
                
                # Route command
                self._process_command(user_input.strip())
            
            except ValueError:
                # Handle IO errors
                break
            except Exception as e:
                # Handle unexpected errors
                self.log.error(f"Input Error: {e}")

    def _process_command(self, raw_input: str):
        """
        Parse and route the user command.

        Args:
            raw_input (str): The full command string typed by the user.
        """
        ## Ignore empty line
        if not raw_input:
            return

        # Sanitize and split
        clean_input = raw_input.strip().upper()
        for phrase, token in MULTI_WORD_TOKENS.items():
            if phrase in clean_input:
                clean_input = clean_input.replace(phrase, token)

        parts = clean_input.split()
        
        cmd = self._normalize_term(parts[0]) 
        args = parts[1:]

        ## Execute command logic
        try:
            # --- SYSTEM CONTROL ---
            if cmd in ["QUIT"]:
                self.log.info("Shutdown command received.")
                self.controller.stop_all(self.scheduler)
                self.running = False

            elif cmd == "STOP":
                print(">> EMERGENCY STOP TRIGGERED")
                self.controller.stop_all(self.scheduler)

            elif cmd == "HELP":
                self._print_help()

            # --- AUTOMATION CYCLES ---
            elif cmd == "CYCLE":
                self._handle_cycle(args)

            # --- MANUAL HARDWARE ---
            elif cmd == "LIGHTS":
                self._handle_lights(args)

            elif cmd == "PUMP":
                self._handle_pump(args)

            # --- MANUAL SENSORS ---

            elif cmd == "RUN":
                self._handle_run(args)

            # --- AUDIO ---
            elif cmd == "MUSIC":
                self._handle_music(args)

            # --- DIAGNOSTICS ---
            elif cmd == "PING":
                self._handle_ping(args)

            elif cmd == "STATUS":
                self._print_status()

            elif cmd == "SYNC":
                print(">> Synchronizing software state with hardware...")
                self.controller.sync_state()
                print(">> Sync Complete.")

            # --- UNKNOWN ---
            else:
                print(f">> Unknown Command: {cmd}")

        except Exception as e:
            # Catch unknown errors
            self.log.error(f"Command Execution Error: {e}")

    def _normalize_term(self, term: str) -> str:
        """
        Normalize a user input term into its canonical system component name.

        Args:
            term (str): The raw input string from the user.

        Returns:
            str: The canonical system name if an alias exists, otherwise returns the original `term` unchanged.
        """
        return COMPONENT_ALIASES.get(term, term)

    # --- COMMAND HANDLERS ---
    def _handle_cycle(self, args: List[str]):
        """
        Handle CYCLE command.
        Usage: CYCLE [COMPONENT] [ON/OFF]
        """
        if len(args) < 2:
            print(">> Usage: CYCLE [COMPONENT] [ON/OFF]")
            print("   Components: LIGHTS, PUMP, ENVIRONMENT, WATER_LEVEL, CAMERA, PI_HEALTH")
            print("   Groups:     SYSTEM, HARDWARE, SENSORS")
            return

        normalized_name = self._normalize_term(args[0])

        component = normalized_name.lower()
        state = args[1].upper() == "ON"
        
        # Enable/Disable cycle
        self.scheduler.set_cycle(component, state)
        print(f">> Cycle '{normalized_name}' set to {'ENABLED' if state else 'DISABLED'}")

    def _handle_pump(self, args: List[str]):
        """
        Handle PUMP command.
        Usage: PUMP [ON/OFF] (DURATION)
        """
        if not args:
            print(">> Usage: PUMP [ON/OFF] <duration_sec>")
            return

        state = args[0] == "ON"
        duration = 0 
        
        if len(args) > 1 and state:
            try:
                duration = int(args[1])
            except ValueError:
                print(">> Error: Duration must be an integer.")
                return
        
        if state and duration == 0:
            print(">> No duration specified. Using default max safety time.")

        # Enable/Disable pump
        self.controller.set_pump(state, duration)
        print(f">> Pump set to {'ON' if state else 'OFF'}")


    def _handle_lights(self, args: List[str]):
        """
        Handle LIGHTS command.
        Usage: LIGHTS [ON/OFF] (DURATION)
        """
        if not args:
            print(">> Usage: LIGHTS [ON/OFF] <duration_sec>")
            return

        state = args[0] == "ON"
        duration = 0
        
        if len(args) > 1 and state:
            try:
                duration = int(args[1])
            except ValueError:
                print(">> Error: Duration must be an integer.")
                return

        # Enable/Disable lights
        self.controller.set_lights(state, duration)
        self.scheduler.register_manual_light_change(state)
        print(f">> Lights set to {'ON' if state else 'OFF'}" + (f" for {duration}s" if duration > 0 else ""))

    def _handle_run(self, args: List[str]):
        """
        Handle RUN command.
        Usage: RUN [COMPONENT]
        """
        if not args:
            print(">> Usage: RUN [SENSORS|ENVIRONMENT|WATER_LEVEL|CAMERA|LIVE_CAMERA|PI_HEALTH]")
            return
            
        target = self._normalize_term(args[0])

        if target == "SENSORS":
            data = self.controller.run_full_diagnostic()

            # Environment
            if data["env"]:
                print(f">> Environment: {data['env'][0]}°F | {data['env'][1]}% RH")
            else:
                print(">> Environment: [TIMEOUT]")

            # Water Level
            if data["water"] is not None:
                print(f">> Water Level: {data['water']}mm")
            else:
                print(">> Water Level: [TIMEOUT]")

            # Pi Health
            print(f">> Pi Health:   {data['pi']}°C")
            
            print(">> Sweep Complete.")
            
        elif target == "ENVIRONMENT":
            print(">> Reading Environment...")
            data = self.controller.read_environment()
            if data:
                print(f">> Temp: {data[0]}F | Humidity: {data[1]}%")
            else:
                print(">> Error: Sensor timeout.")

        elif target == "WATER_LEVEL":
            print(">> Reading Water Level...")
            level = self.controller.read_water_level()
            if level is not None:
                print(f">> Water Level: {level}mm")
            else:
                print(">> Error: Sensor timeout.")

        elif target == "CAMERA":
            # Check for optional count argument
            count = None
            if len(args) > 1:
                try:
                    count = int(args[1])
                except ValueError:
                    print(">> Error: Count must be an integer.")
                    return
            
            # If count is None, controller will use settings default
            count_str = f"{count}" if count else "Default"
            print(f">> Capturing images (Count: {count_str})...")
            
            files = self.controller.capture_smart_image(count=count)
            
            if files:
                print(f">> Saved {len(files)} images: {files}")
            else:
                print(">> Error: Camera failed.")

        elif target == "LIVE_CAMERA":
            duration = 0
            
            if len(args) > 1:
                try:
                    duration = int(args[1])
                except ValueError:
                    print(">> Error: Duration must be an integer.")
                    return
            if duration == 0:
                print(">> Starting Live Camera (Indefinite).")
                print(">> Close the video window to return to CLI.")
            else:
                print(f">> Starting Live Camera for {duration}s...")
                
            self.controller.run_live_camera(duration)
            print(">> Live View Closed.")

        elif target == "PI_HEALTH":
            print(">> Checking Pi Health...")
            temp = self.controller.check_pi_health()
            print(f">> CPU Temp: {temp}C")
            
        else:
            print(f">> Unknown Run Target: {target}")

    def _handle_music(self, args: List[str]):
        """
        Handle MUSIC command.
        Usage: MUSIC [PLAY/STOP] <song_name>
        """
        if not args:
            print(">> Usage: MUSIC [PLAY <song> | STOP | LIST]")
            return

        action = args[0].upper()

        if action == "LIST":
            print("\n--- AEROSENSE JUKEBOX ---")
            print("Available Songs:")
            print("  * DAISY")
            print("  * CURIOSITY")
            print("  * ULTRON")
            print("  * MV1")
            print("  * TARS")
            print("  * PANIC")
            print("  * MORNING")
            print("  * SLEEP")
            print("  * FNAF")
            print("  * TEST")
            print("  * GRANTED")
            print("  * DENIED")
            print("\nAvailable Notes (Octaves 3-8):")
            print("  * Octave 3: C3, CS3, D3, DS3, E3, F3, FS3, G3, GS3, A3, AS3, B3")
            print("  * Octave 4: C4, CS4, D4, DS4, E4, F4, FS4, G4, GS4, A4, AS4, B4")
            print("  * Octave 5: C5, CS5, D5, DS5, E5, F5, FS5, G5, GS5, A5, AS5, B5")
            print("  * Octave 6: C6, CS6, D6, DS6, E6, F6, FS6, G6, GS6, A6, AS6, B6")
            print("  * Octave 7: C7, CS7, D7, DS7, E7, F7, FS7, G7, GS7, A7, AS7, B7")
            print("  * Octave 8: C8")
            print("\n  (Note: 'S' = Sharp. Use CS4 for C#4)")
            print("-------------------------\n")

        elif action == "PLAY":
            if len(args) < 2:
                print(">> Usage: MUSIC PLAY [SONG] OR MUSIC PLAY NOTE [NOTE] [SEC]")
                return
            
            full_arg = " ".join(args[1:]) 
            command = f"MUSIC PLAY {full_arg}"
            
            self.controller.arduino.send(command)
            print(f">> Sent: {command}")

        elif action == "STOP":
            self.controller.stop_music()
            print(">> Music Stopped.")
            
        else:
            print(f">> Unknown Music Action: {action}")
    
    def _handle_ping(self, args: List[str]):
        """
        Handle PING command with groups.
        Usage: PING [COMPONENT]
        """
        if not args:
            print(">> Usage: PING [HARDWARE | SENSORS | PUMP | LIGHTS | MUSIC | ENVIRONMENT | WATER_LEVEL | CAMERA]")
            return

        target = self._normalize_term(args[0])

        # --- Hardware ---
        if target == "HARDWARE":
            print("\n--- HARDWARE STATUS ---")
            print(f"Pump:     {self.controller.ping_component('PUMP')}")
            print(f"Lights:   {self.controller.ping_component('LIGHTS')}")
            print(f"Music:    {self.controller.ping_component('MUSIC')}")
            print("-----------------------")

        # --- Sensors ---
        elif target == "SENSORS":
            print("\n--- SENSOR STATUS ---")
            print(f"Env:      {self.controller.ping_component('TEMP')}")
            print(f"Water:    {self.controller.ping_component('DIST')}")
            print(f"Camera:   {self.controller.ping_component('CAMERA')}")
            print("---------------------")

        # --- Individual Component ---
        else:
            print(f">> Pinging {target}...")
            result = self.controller.ping_component(target)
            print(f">> Response: {result}")

    def _print_status(self):
        """
        Print a formatted system report checking Cycles and Hardware.
        """
        print("\n--- SYSTEM STATUS ---")
        
        # --- Automation Cycles ---
        print("CYCLES:")
        cycles = self.scheduler.cycles
        fmt = lambda x: "[ON]" if x else "[OFF]"

        print(f"  PUMP:         {fmt(cycles.get('pump'))}")
        print(f"  LIGHTS:       {fmt(cycles.get('lights'))}")
        print(f"  ENVIRONMENT:  {fmt(cycles.get('environment'))}")
        print(f"  WATER_LEVEL:  {fmt(cycles.get('water_level'))}")
        print(f"  CAMERA:       {fmt(cycles.get('camera'))}")
        print(f"  PI_HEALTH:    {fmt(cycles.get('pi_health'))}")
        print("")

        # --- Hardware ---
        print("HARDWARE:")
        
        # Pump
        p_res = self.controller.ping_component("PUMP")
        p_state = "[ON]" if "ON" in p_res else "[OFF]"
        print(f"  PUMP:         {p_state}")

        # Lights
        l_res = self.controller.ping_component("LIGHTS")
        l_state = "[ON]" if "ON" in l_res else "[OFF]"
        print(f"  LIGHTS:       {l_state}")

        # Audio
        m_res = self.controller.ping_component("MUSIC")
        m_state = "[ACTIVE]" if "BUSY" in m_res else "[QUIET]"
        print(f"  AUDIO:        {m_state}")
        print("")

        # Sensors
        def check_resp(tag):
            res = self.controller.ping_component(tag)
            is_ok = any(x in res for x in ["OK", "IDLE", "BUSY"])
            return "[RESPONDING]" if is_ok else "[NOT RESPONDING]"

        print(f"  ENVIRONMENT:  {check_resp('TEMP')}")
        print(f"  WATER_LEVEL:  {check_resp('DIST')}")
        print(f"  CAMERA:       {check_resp('CAMERA')}")
        
        print("---------------------\n")

    def _print_help(self):
        """
        Print the help menu.
        """
        print("""
--- COMMAND LIST ---
CYCLES (AUTOMATION):
  CYCLE SYSTEM [ON/OFF]   - Enable/Disable all cycles
  CYCLE HARDWARE [ON/OFF] - Enable/Disable Pump and Lights cycles
  CYCLE SENSORS [ON/OFF]  - Enable/Disable Environment, Water Level, Camera, and Pi Health cycles
  
  INDIVIDUAL:
  CYCLE PUMP [ON/OFF]     - Enable/Disable Pump cycle
  CYCLE LIGHTS [ON/OFF]   - Enable/Disable Lights cycle
  CYCLE ENVIRONMENT [ON/OFF] - Enable/Disable Environment cycle
  CYCLE WATER_LEVEL [ON/OFF] - Enable/Disable Water Level cycle
  CYCLE CAMERA [ON/OFF] - Enable/Disable Camera cycle
  CYCLE PI_HEALTH [ON/OFF] - Enable/Disable Pi Health cycle                

              
HARDWARE (MANUAL):
  LIGHTS ON [SEC]        - Turn lights on (0s for indefinite)
  LIGHTS OFF             - Turn lights off
  PUMP ON [SEC]          - Turn pump on (0s for 30s max)
  PUMP OFF               - Turn pump off


SENSORS (MANUAL):
  RUN SENSORS            - Run Environment, Water Level, Camera, and Pi Health
  RUN ENVIRONMENT        - Read Temperature & Humidity
  RUN WATER LEVEL        - Read Water Level
  RUN CAMERA [COUNT]     - Capture image(s) (3s is Default)
  RUN PI HEALTH          - Check CPU Temp
              
  RUN LIVE CAMERA [SEC]  - Open live video preview (0s for indefinite)

                      
AUDIO
  MUSIC PLAY [SONG/NOTE] - Play a song
  MUSIC PLAY NOTE [NOTE] [SEC] - Play a note (1s is Default)
  MUSIC PLAY RANDOM      - Play a random song
  MUSIC LIST             - List all songs and notes
  MUSIC STOP             - Stop buzzer         


DIAGNOSTICS
  STATUS                 - Show system status
  SYNC  - Ensure entire system is synced

  PING SYSTEM - Ping Arduino
                            
  PING HARDWARE - Ping Pump and Lights
  PING PUMP - Ping Pump   
  PING LIGHTS - Ping Lights

  PING SENSORS - Ping Environment, Water Level, and Camera             
  PING ENVIRONMENT - Ping Environment sensor                           
  PING WATER LEVEL - Ping Water Level sensor
  PING CAMERA - Ping Camera module

                          
SYSTEM:
  STOP                   - Emergency Stop
  EXIT                   - Shutdown
""")