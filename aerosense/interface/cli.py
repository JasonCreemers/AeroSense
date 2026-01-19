"""
AeroSense Command Line Interface.

This module acts as the user interface layer for the system. 
It processes input from the console, routes commands to the appropriate system logic, and provides real-time feedback to the operator.
"""

import logging
import sys
import textwrap
import threading
from typing import List

from aerosense.core.controller import Controller
from aerosense.core.scheduler import Scheduler
from aerosense.interface.web import WebServer

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

    "WEB": "GUI",
    "INTERFACE": "GUI",

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

    def __init__(self, controller: Controller, scheduler: Scheduler, web_server: WebServer):
        """
        Initialize the CLI.

        Args:
            controller (Controller): The active system controller instance.
            scheduler (Scheduler): The active system scheduler instance.
        """
        self.controller = controller
        self.scheduler = scheduler
        self.web_interface = web_server
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
                self.controller.play_music("DENIED")

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

            elif cmd == "GUI":
                # Check if server is running and start if not
                if not self.web_interface.is_running:
                    print(">> Initializing Web Server...")
                    self.web_interface.start()
                    import time
                    time.sleep(1.0)
                
                url = f"http://127.0.0.1:{self.web_interface.port}"
                
                # Print the URL
                print(f"\n>> ---------------------------------------------------")
                print(f">> WEB INTERFACE READY")
                print(f">> Access URL: {url}")
                print(f">> (Ctrl+Click the link above to open in your browser)")
                print(f">> ---------------------------------------------------\n")

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

            elif cmd == "RESET":
                self.scheduler.reset_overrides()
                print(">> Manual overrides cleared. Resuming automation.")

            # --- UNKNOWN ---
            else:
                print(f">> Unknown Command: {cmd}")
                self.controller.play_music("DENIED")

        except Exception as e:
            # Catch unknown errors
            self.log.error(f"Command Execution Error: {e}")
            self.controller.play_music("DENIED")

    def _normalize_term(self, term: str) -> str:
        """
        Normalize a user input term into its canonical system component name.

        Args:
            term (str): The raw input string from the user.

        Returns:
            str: The canonical system name if an alias exists, otherwise returns the original `term` unchanged.
        """
        return COMPONENT_ALIASES.get(term, term)
    
    def _parse_arg(self, args: List[str], index: int, default=None):
        """
        Helper to safely get an integer argument or return a default.

        Args:
            args (List[str]): The list of arguments provided by the user.
            index (int): The index of the argument to parse.
            default (Optional[int]): The value to return if the argument is missing.

        Returns:
            Optional[int]: The parsed integer, the default value, or None on error.
        """
        if len(args) > index:
            try:
                return int(args[index])
            except ValueError:
                print(">> Error: Argument must be an integer.")
                self.controller.play_music("DENIED")
                return None
        return default

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
        duration = self._parse_arg(args, 1, default=0) 
        
        if duration is not None:
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
        duration = self._parse_arg(args, 1, default=0)

        # Enable/Disable lights
        if duration is not None:
            self.controller.set_lights(state, duration)
            self.scheduler.register_manual_light_change(state)
            suffix = f" for {duration}s" if duration > 0 else ""
            print(f">> Lights set to {'ON' if state else 'OFF'}{suffix}")

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
            env_str = f"{data['env'][0]}°F | {data['env'][1]}% RH" if data['env'] else "[TIMEOUT]"
            water_str = f"{data['water']}mm" if data['water'] is not None else "[TIMEOUT]"
            if isinstance(data['pi'], dict):
                 pi_str = (f"Temp: {data['pi']['temp']}°C | "
                           f"RAM: {data['pi']['ram']}% | "
                           f"Disk: {data['pi']['disk']}GB | "
                           f"Up: {data['pi']['uptime']}hr")
            else:
                 pi_str = "[ERROR]"

            print(f"\n--- DIAGNOSTIC SWEEP ---")
            print(f">> Environment: {env_str}")
            print(f">> Water Level: {water_str}")
            print(f">> Pi Health:   {pi_str}")
            print("------------------------")

        elif target == "ENVIRONMENT":
            print(">> Reading Environment...")
            data = self.controller.read_environment()
            print(f">> Temp: {data[0]}F | Humidity: {data[1]}%" if data else ">> Error: Sensor timeout.")

        elif target == "WATER_LEVEL":
            print(">> Reading Water Level...")
            level = self.controller.read_water_level()
            print(f">> Water Level: {level}mm" if level is not None else ">> Error: Sensor timeout.")

        elif target == "CAMERA":
            count = self._parse_arg(args, 1, default=-1)
            if count is None: return
            
            final_count = None if count == -1 else count
            
            count_str = f"{final_count}" if final_count else "Default"
            print(f">> Capturing images (Count: {count_str})...")
            
            files = self.controller.capture_smart_image(count=final_count)
            print(f">> Saved {len(files)} images: {files}" if files else ">> Error: Camera failed.")

        elif target == "LIVE_CAMERA":
            duration = self._parse_arg(args, 1, default=0)
            if duration is None: return
            
            if duration == 0:
                print(">> Starting Live Camera (Indefinite).")
                print(">> Close the video window to return to CLI.")
            else:
                print(f">> Starting Live Camera for {duration}s...")
                
            t = threading.Thread(
                target=self.controller.run_live_camera, 
                args=(duration,), 
                daemon=True
            )
            t.start()

        elif target == "PI_HEALTH":
            print(">> Checking Pi Health...")
            data = self.controller.check_pi_health()
            
            print(f"   CPU Temp:   {data['temp']}°C")
            print(f"   RAM Usage:  {data['ram']}%")
            print(f"   Disk Free:  {data['disk']} GB")
            print(f"   Uptime:     {data['uptime']} Hours")
            
        else:
            print(f">> Unknown Run Target: {target}")
            self.controller.play_music("DENIED")

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
            
            # Songs
            print("Available Songs:")
            song_txt = ", ".join(core_ctrl.VALID_SONGS)
            print(textwrap.fill(song_txt, width=60, initial_indent="  ", subsequent_indent="  "))
            
            print("\nAvailable Notes:")
            all_notes = core_ctrl.VALID_NOTES
            for oct_idx in range(3, 9):
                notes_in_octave = [n for n in all_notes if str(oct_idx) in n]
                if notes_in_octave:
                    print(f"  * Octave {oct_idx}: {', '.join(notes_in_octave)}")

            print("\n  (Note: 'S' = Sharp. Use CS4 for C#4)")
            print("-------------------------\n")

        elif action == "PLAY":
            if len(args) < 2:
                print(">> Usage: MUSIC PLAY [SONG] OR MUSIC PLAY NOTE [NOTE] [SEC]")
                return
            
            target = args[1].upper()

            # Note command
            if target == "NOTE":
                if len(args) < 3:
                    print(">> Usage: MUSIC PLAY NOTE [NOTE] [SEC]")
                    return
                note_name = args[2].upper()
                
                if note_name in core_ctrl.VALID_NOTES:
                    duration = self._parse_arg(args, 3, default=1)
                    self.controller.arduino.send(f"MUSIC PLAY NOTE {note_name} {duration}")
                    print(f">> Playing Note: {note_name} ({duration}s)")
                else:
                    print(f">> Invalid Note: {note_name}")
                    self.controller.play_music("DENIED")

            # Random song
            elif target == "RANDOM":
                 self.controller.play_music("RANDOM")
                 print(">> Playing Random Track")

            # Song
            elif target in core_ctrl.VALID_SONGS:
                self.controller.play_music(target)
                print(f">> Playing Song: {target}")

            else:
                print(f">> Invalid Song: '{target}'. Type 'MUSIC LIST' for options.")
                self.controller.play_music("DENIED")

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
            p = self.controller.ping_component('PUMP')
            l = self.controller.ping_component('LIGHTS')
            m = self.controller.ping_component('MUSIC')
            
            print(f"Pump:     {p}")
            print(f"Lights:   {l}")
            print(f"Music:    {m}")
            print("-----------------------")
            # Only play sound if all are communicating
            if "TIMEOUT" not in (p + l + m) and "ERROR" not in (p + l + m):
                 self.controller.play_music("GRANTED")
            else:
                 self.controller.play_music("DENIED")

        # --- Sensors ---
        elif target == "SENSORS":
            print("\n--- SENSOR STATUS ---")
            t = self.controller.ping_component('TEMP')
            d = self.controller.ping_component('DIST')
            c = self.controller.ping_component('CAMERA')
            
            print(f"Env:      {t}")
            print(f"Water:    {d}")
            print(f"Camera:   {c}")
            print("---------------------")
            
            if "TIMEOUT" not in (t + d + c) and "ERROR" not in (t + d + c):
                 self.controller.play_music("GRANTED")
            else:
                 self.controller.play_music("DENIED")

        # --- Individual Component ---
        else:
            print(f">> Pinging {target}...")
            result = self.controller.ping_component(target)
            print(f">> Response: {result}")

            if "TIMEOUT" in result or "ERROR" in result:
                self.controller.play_music("DENIED")
            else:
                self.controller.play_music("GRANTED")

    def _print_status(self):
        """
        Print a formatted system report checking Cycles and Hardware.
        """
        print("\n--- SYSTEM STATUS ---")
        
        # --- Automation Cycles ---
        print("CYCLES:")
        cycles = self.scheduler.cycles
        fmt = lambda x: "[ON]" if x else "[OFF]"

        # Check for overrides
        light_status = fmt(cycles.get('lights'))
        if self.scheduler.manual_override_on:
            light_status += " [MANUAL: FORCE ON]"
        elif self.scheduler.manual_override_off:
            light_status += " [MANUAL: FORCE OFF]"

        print(f"  PUMP:         {fmt(cycles.get('pump'))}")
        print(f"  LIGHTS:       {light_status}")
        print(f"  ENVIRONMENT:  {fmt(cycles.get('environment'))}")
        print(f"  WATER_LEVEL:  {fmt(cycles.get('water_level'))}")
        print(f"  CAMERA:       {fmt(cycles.get('camera'))}")
        print(f"  PI_HEALTH:    {fmt(cycles.get('pi_health'))}")
        print("")

        # --- Hardware ---
        print("HARDWARE:")
        
        # Helper to format status and catch errors
        def get_hw_status(raw_res, on_key="ON"):
            if "TIMEOUT" in raw_res or "ERROR" in raw_res:
                return "[TIMEOUT/ERROR]"
            return f"[{on_key}]" if on_key in raw_res else "[OFF]"

        # Pump
        p_res = self.controller.ping_component("PUMP")
        print(f"  PUMP:         {get_hw_status(p_res, 'ON')}")

        # Lights
        l_res = self.controller.ping_component("LIGHTS")
        print(f"  LIGHTS:       {get_hw_status(l_res, 'ON')}")

        # Audio
        m_res = self.controller.ping_component("MUSIC")
        if "TIMEOUT" in m_res or "ERROR" in m_res:
            m_state = "[TIMEOUT/ERROR]"
        else:
            m_state = "[ACTIVE]" if "BUSY" in m_res else "[QUIET]"
        print(f"  AUDIO:        {m_state}")
        print("")

        # --- Sensors ---
        def check_sensor(tag):
            res = self.controller.ping_component(tag)
            is_ok = any(x in res for x in ["OK", "IDLE", "BUSY"])
            return "[RESPONDING]" if is_ok else "[NOT RESPONDING]"

        env_stat = check_sensor('TEMP')
        wat_stat = check_sensor('DIST')
        cam_stat = check_sensor('CAMERA')
        
        print(f"  ENVIRONMENT:  {env_stat}")
        print(f"  WATER_LEVEL:  {wat_stat}")
        print(f"  CAMERA:       {cam_stat}")
        
        print("---------------------\n")

        # Check status for alert
        all_raw = p_res + l_res + m_res
        all_stats = env_stat + wat_stat + cam_stat
        
        if "TIMEOUT" in all_raw or "ERROR" in all_raw or "NOT RESPONDING" in all_stats:
            self.controller.play_music("DENIED")
        else:
            self.controller.play_music("GRANTED")

    def _print_help(self):
        """
        Print the help menu.
        """
        print("""
--- COMMAND LIST ---
CYCLES (AUTOMATION):
  CYCLE SYSTEM [ON/OFF]        - Enable/Disable all cycles
  CYCLE HARDWARE [ON/OFF]      - Enable/Disable Pump and Lights cycles
  CYCLE SENSORS [ON/OFF]       - Enable/Disable Environment, Water Level, Camera, and Pi Health cycles
  
  INDIVIDUAL:
  CYCLE PUMP [ON/OFF]          - Enable/Disable Pump cycle
  CYCLE LIGHTS [ON/OFF]        - Enable/Disable Lights cycle
  CYCLE ENVIRONMENT [ON/OFF]   - Enable/Disable Environment cycle
  CYCLE WATER_LEVEL [ON/OFF]   - Enable/Disable Water Level cycle
  CYCLE CAMERA [ON/OFF]        - Enable/Disable Camera cycle
  CYCLE PI_HEALTH [ON/OFF]     - Enable/Disable Pi Health cycle

              
HARDWARE (MANUAL):
  LIGHTS ON [SEC]              - Turn lights on (0s for indefinite)
  LIGHTS OFF                   - Turn lights off
  PUMP ON [SEC]                - Turn pump on (0s for 30s max)
  PUMP OFF                     - Turn pump off


SENSORS (MANUAL):
  RUN SENSORS                  - Run Environment, Water Level, Camera, and Pi Health
  RUN ENVIRONMENT              - Read Temperature & Humidity
  RUN WATER LEVEL              - Read Water Level
  RUN CAMERA [COUNT]           - Capture image(s) (3s is Default)
  RUN PI HEALTH                - Check CPU Temp
              
  RUN LIVE CAMERA [SEC]        - Open live video preview (0s for indefinite)

                      
AUDIO
  MUSIC PLAY [SONG/NOTE]       - Play a song
  MUSIC PLAY NOTE [NOTE] [SEC] - Play a note (1s is Default)
  MUSIC PLAY RANDOM            - Play a random song
  MUSIC LIST                   - List all songs and notes
  MUSIC STOP                   - Stop buzzer


DIAGNOSTICS
  STATUS                       - Show system status
  SYNC                         - Ensure entire system is synced
  RESET                        - Clear manual overrides

  PING SYSTEM                  - Ping Arduino
                            
  PING HARDWARE                - Ping Pump and Lights
  PING PUMP                    - Ping Pump   
  PING LIGHTS                  - Ping Lights

  PING SENSORS                 - Ping Environment, Water Level, and Camera             
  PING ENVIRONMENT             - Ping Environment sensor                           
  PING WATER LEVEL             - Ping Water Level sensor
  PING CAMERA                  - Ping Camera module

                          
SYSTEM:
  GUI                          - Open a web based GUI
  STOP                         - Emergency Stop
  EXIT                         - Shutdown
""")