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
from typing import Optional

from aerosense.core.controller import Controller
from aerosense.core.scheduler import Scheduler
from config import settings

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
        project_root = current_dir.parent.parent  # Go up to 'AeroSense' root
        
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
            self.log.error(f"Web Server crashed: {e}")
            self.is_running = False

    def _register_routes(self):
        """
        Bind URL rules to internal handler methods.
        """
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/api/cycles', 'get_cycles', self.get_cycles)
        self.app.add_url_rule('/api/toggle_cycle', 'toggle_cycle', self.toggle_cycle, methods=['POST'])
        self.app.add_url_rule('/api/capture', 'capture', self.run_capture, methods=['POST'])
        self.app.add_url_rule('/api/live', 'live', self.run_live, methods=['POST'])
        self.app.add_url_rule('/api/action', 'action', self.run_action, methods=['POST'])
        self.app.add_url_rule('/images/<path:filename>', 'images', self.serve_image)

    # --- View Logic ---
    def index(self):
        """
        Render the main dashboard.

        Returns:
            str: Rendered HTML template with current system status.
        """
        # Find most recent image for display
        images = sorted(Path(settings.IMG_DIR).glob('*.jpg'), key=os.path.getmtime, reverse=True)
        latest_img = images[0].name if images else None
        
        img_time = "No images found"
        if latest_img:
            timestamp = os.path.getmtime(images[0])
            mins = int((time.time() - timestamp) / 60)
            img_time = f"{mins} mins ago"

        status_lines = self._generate_status_text()
        
        return render_template('index.html', 
                               latest_image=latest_img, 
                               img_time=img_time,
                               status_text=status_lines)

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
        API: Enable or disable specific automation cycles.
        Accepts JSON: {"target": "LIGHTS"} or {"target": "ALL_ON"}
        """
        data = request.json
        target = data.get('target')
        
        if target == "ALL_ON":
            self.scheduler.set_cycle("system", True)
        elif target == "ALL_OFF":
            self.scheduler.set_cycle("system", False)
        else:
            current = self.scheduler.cycles.get(target, False)
            self.scheduler.set_cycle(target, not current)
            
        return jsonify(success=True)

    def run_capture(self):
        """
        API: Trigger a background camera capture sequence.
        """
        self.controller.capture_smart_image(blocking=False)
        return jsonify(success=True, message="Capture started")

    def run_live(self):
        """
        API: Launch the live camera preview on the host HDMI display.
        """
        threading.Thread(target=self.controller.run_live_camera, args=(0,), daemon=True).start()
        return jsonify(success=True, message="Live feed started on Main Display")

    def run_action(self):
        """
        API: Execute system-level actions (SYNC, RESET).
        """
        action = request.json.get('action')
        
        if action == "SYNC":
            self.controller.sync_state()
        elif action == "RESET":
            self.scheduler.reset_overrides()
        
        return jsonify(success=True)

    def _generate_status_text(self) -> str:
        """
        Generate a text-based system report for the dashboard.
        
        Returns:
            str: Multiline string mimicking the CLI 'STATUS' command.
        """
        lines = []
        lines.append("--- SYSTEM STATUS ---")
        lines.append(f"Time: {time.strftime('%H:%M:%S')}")
        lines.append("")
        
        lines.append("CYCLES:")
        for k, v in self.scheduler.cycles.items():
            lines.append(f"  {k.upper()}: {'[ON]' if v else '[OFF]'}")
            
        lines.append("")
        lines.append("HARDWARE STATE (PYTHON):")
        pump = self.controller.state['pump']
        lights = self.controller.state['lights']
        lines.append(f"  PUMP:   {'[ACTIVE]' if pump else '[OFF]'}")
        lines.append(f"  LIGHTS: {'[ACTIVE]' if lights else '[OFF]'}")
        
        return "\n".join(lines)