"""
AeroSense Web Interface.

This module hosts a local Flask server to provide a Graphical User Interface (GUI) for the system.
It exposes API endpoints that allow a web browser to interact with the Controller and Scheduler 
in real-time, mirroring the capabilities of the CLI.
"""

import logging
import os
import threading
import time
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from typing import Optional, List, Dict, Any

from aerosense.core.controller import Controller
from aerosense.core.scheduler import Scheduler
from config import settings

SONG_LIST = [
    "Daisy", "Curiosity", "Ultron", "MV1", "Tars", "Panic", 
    "Morning", "Sleep", "Fnaf", "Test", "Granted", "Denied"
]

class WebServer:
    """
    Manages the Flask application server in a background thread.

    Attributes:
        controller (Controller): Reference to the main system controller.
        scheduler (Scheduler): Reference to the automation scheduler.
        app (Flask): The underlying Flask application instance.
        port (int): The network port to bind to (default: 5000).
        is_running (bool): Flag indicating if the server thread is active.
        log (logging.Logger): Dedicated logger for web interface events.
    """

    def __init__(self, controller: Controller, scheduler: Scheduler):
        """
        Initialize the WebServer with system references.

        Args:
            controller (Controller): The active system controller instance.
            scheduler (Scheduler): The active system scheduler instance.
        """
        self.controller = controller
        self.scheduler = scheduler
        self.log = logging.getLogger("AeroSense.Interface.Web")
        
        # Configure Flask paths relative to this module location
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent.parent
        
        template_dir = project_root / "templates"
        data_dir = project_root / "data"

        self.app = Flask(
            __name__, 
            template_folder=str(template_dir), 
            static_folder=str(data_dir)
        )
        
        self.port = 5000
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        
        # Route registration
        self._register_routes()

    def start(self):
        """
        Start the Flask server in a daemon thread if it is not already running.
        """
        if self.is_running:
            self.log.warning("Web server is already active.")
            return

        self.log.info(f"Starting Web Interface on port {self.port}...")
        self.is_running = True
        
        self._thread = threading.Thread(target=self._run_server, daemon=True)
        self._thread.start()

    def _run_server(self):
        """
        Internal entry point for the server thread.
        Disables the default Werkzeug logger to keep the CLI clean.
        """
        # Suppress Flask CLI output
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        try:
            self.app.run(
                host='0.0.0.0', 
                port=self.port, 
                debug=False, 
                use_reloader=False
            )
        except Exception as e:
            # Catch web errors
            self.log.error(f"Web Server crashed: {e}")
            self.is_running = False

    def _register_routes(self):
        """
        Bind URL rules to internal handler methods.
        """
        # View Routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/images/<path:filename>', 'images', self.serve_image)
        
        # API Routes - Automation
        self.app.add_url_rule('/api/cycles', 'get_cycles', self.get_cycles)
        self.app.add_url_rule('/api/toggle_cycle', 'toggle_cycle', self.toggle_cycle, methods=['POST'])
        self.app.add_url_rule('/api/toggle_group', 'toggle_group', self.toggle_cycle_group, methods=['POST'])
        
        # API Routes - Hardware & Sensors
        self.app.add_url_rule('/api/run_manual', 'run_manual', self.run_manual, methods=['POST'])
        self.app.add_url_rule('/api/run_sensor', 'run_sensor', self.run_sensor, methods=['POST'])
        
        # API Routes - Diagnostics & Utilities
        self.app.add_url_rule('/api/music', 'music', self.control_music, methods=['POST'])
        self.app.add_url_rule('/api/ping', 'ping', self.ping_component, methods=['POST'])
        self.app.add_url_rule('/api/system', 'system', self.system_command, methods=['POST'])

    # --- Helpers ---
    def _fmt_time(self, timestamp: float) -> str:
        """
        Format a timestamp into a human-readable 'time ago' string.

        Args:
            timestamp (float): The epoch timestamp to format.

        Returns:
            str: e.g., "5s ago", "2m ago", "1h ago", or "Never".
        """
        if timestamp == 0: return "Never"
        diff = time.time() - timestamp
        if diff < 60: return f"{int(diff)}s ago"
        if diff < 3600: return f"{int(diff/60)}m ago"
        return f"{int(diff/3600)}h ago"

    # --- View Logic ---
    def index(self):
        """
        Render the main dashboard.

        Returns:
            str: Rendered HTML template with current system status and cache data.
        """
        # Find most recent image in cache
        img_data = self.controller.data_cache.get("latest_photo", {})
        latest_img = img_data.get("value")
        img_time = self._fmt_time(img_data.get("timestamp", 0))

        # Format the entire controller cache for display
        formatted_cache = {}
        for k, v in self.controller.data_cache.items():
            val = v['value']
            if isinstance(val, float): val = round(val, 2)
            
            formatted_cache[k] = {
                "value": val if val is not None else "--",
                "time": self._fmt_time(v['timestamp'])
            }

        return render_template('index.html', 
                               latest_image=latest_img, 
                               img_time=img_time,
                               cache=formatted_cache,
                               cycles=self.scheduler.cycles,
                               songs=SONG_LIST)

    def serve_image(self, filename: str):
        """
        Serve an image file from the data directory.

        Args:
            filename (str): The name of the file to serve.
        """
        return send_from_directory(settings.IMG_DIR, filename)

    # --- API Handlers ---
    def get_cycles(self):
        """
        API: Retrieve the current state of automation cycles.
        """
        return jsonify(self.scheduler.cycles)
    
    def toggle_cycle(self):
        """
        API: Toggle a specific automation cycle.
        Expects JSON: {"target": "lights"}
        """
        data = request.json
        target = data.get('target')
        current = self.scheduler.cycles.get(target, False)
        self.scheduler.set_cycle(target, not current)
        return jsonify(success=True)

    def toggle_cycle_group(self):
        """
        API: Smart toggle for cycle groups (SYSTEM, HARDWARE, SENSORS).
        
        Logic: 
        If ALL items in the group are ON -> Turn them ALL OFF.
        If ANY item in the group is OFF -> Turn them ALL ON (Sync/Correct).
        
        Expects JSON: {"group": "hardware"}
        """
        group_name = request.json.get('group')
        
        groups = {
            "hardware": ["lights", "pump"],
            "sensors": ["environment", "water_level", "camera", "pi_health"],
            "system": ["lights", "pump", "environment", "water_level", "camera", "pi_health"]
        }
        
        target_keys = groups.get(group_name, [])
        
        # Check if ALL are currently ON
        all_on = all(self.scheduler.cycles.get(k) for k in target_keys)
        
        # Determine new state
        new_state = False if all_on else True
        
        for k in target_keys:
            self.scheduler.set_cycle(k, new_state)
            
        return jsonify(success=True)
    
    def run_action(self):
        """
        API: Execute general system actions (SYNC, RESET).
        Expects JSON: {"action": "SYNC"} or {"action": "RESET"}
        """
        action = request.json.get('action')
        
        if action == "SYNC":
            self.controller.sync_state()
        elif action == "RESET":
            self.scheduler.reset_overrides()
        
        return jsonify(success=True)
    
    def run_manual(self):
        """
        API: Manually trigger hardware actuators (Lights/Pump).
        Expects JSON: {"target": "LIGHTS", "state": "ON", "duration": 60}
        """
        data = request.json
        target = data.get('target')
        state = (data.get('state') == "ON")
        duration = int(data.get('duration', 0))

        if target == "LIGHTS":
            self.controller.set_lights(state, duration)
        elif target == "PUMP":
            self.controller.set_pump(state, duration)
            
        return jsonify(success=True)
    
    def run_sensor(self):
        """
        API: Trigger immediate sensor readings or camera tasks.
        Expects JSON: {"target": "ENVIRONMENT"}
        """
        target = request.json.get('target')
        
        if target == "SENSORS":
            self.controller.run_full_diagnostic()
        elif target == "ENVIRONMENT":
            self.controller.read_environment()
        elif target == "WATER_LEVEL":
            self.controller.read_water_level()
        elif target == "PI_HEALTH":
            self.controller.check_pi_health()
        elif target == "CAMERA":
            self.controller.capture_smart_image(blocking=False)
        elif target == "LIVE_CAMERA":
            threading.Thread(target=self.controller.run_live_camera, args=(0,), daemon=True).start()

        return jsonify(success=True)

    def control_music(self):
        """
        API: Control the music player.
        Expects JSON: {"action": "PLAY", "song": "Daisy"} 
                   or {"action": "STOP"}
        """
        action = request.json.get('action') 
        song = request.json.get('song', "")
        
        if action == "STOP":
            self.controller.stop_music()
        elif action == "RANDOM":
            self.controller.play_music("RANDOM")
        elif action == "PLAY":
            self.controller.play_music(song)
            
        return jsonify(success=True)

    def ping_component(self):
        """
        API: Ping a specific component or a group of components.
        Results are updated in the Controller's cache.
        Expects JSON: {"target": "PUMP"} or {"target": "HARDWARE"}
        """
        target = request.json.get('target')
        
        # Handle Groups via iteration
        groups = {
            "HARDWARE": ["PUMP", "LIGHTS"],
            "SENSORS": ["ENVIRONMENT", "WATER_LEVEL", "CAMERA"],
            "SYSTEM": ["SYSTEM"]
        }

        if target in groups:
            for t in groups[target]:
                if t == "SYSTEM": 
                    self.controller.ping_component("SYSTEM")
                else:
                    self.controller.ping_component(t)
        else:
            self.controller.ping_component(target)
            
        return jsonify(success=True)

    def system_command(self):
        """
        API: Execute system-level commands (STOP, EXIT).
        Expects JSON: {"command": "STOP"}
        """
        cmd = request.json.get('command')
        
        if cmd == "STOP":
            self.controller.stop_all(self.scheduler)
            
        elif cmd == "EXIT":
            self.controller.stop_all(self.scheduler)
            self.log.info("Remote shutdown requested via Web Interface.")
            os._exit(0)
            
        return jsonify(success=True)