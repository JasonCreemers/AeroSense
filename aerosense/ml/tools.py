"""
MOSS Tool Definitions.

This module defines the tools available to the MOSS AI agent.
Each tool has an Ollama-compatible schema and a handler function
that wraps existing Controller methods or reads system data.
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import settings


# --- Ollama Tool Schemas ---
# These define what the LLM sees and can call.

TOOL_SCHEMAS: List[Dict] = [
    {
        "type": "function",
        "function": {
            "name": "read_environment",
            "description": "Read the current temperature (Fahrenheit) and humidity (% RH) from the DHT22 sensor. Returns live data from the Arduino.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_water_level",
            "description": "Read the current water level from the ultrasonic sensor. Returns distance in mm — lower number means more water, higher means less. Over 100mm is critically low.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_pi_health",
            "description": "Check the Raspberry Pi system health: CPU temperature (Celsius), RAM usage (%), free disk space (GB), and uptime (hours).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_vision",
            "description": "Run the full computer vision pipeline: capture image, split into tiles, analyze for plant diseases and green coverage. This is a heavy operation that takes 10-30 seconds.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_plant_health",
            "description": "Run the full plant health classification pipeline: vision capture, environment sensors, feature computation, and XGBoost prediction. Returns a health class (Healthy, Underwatered, etc.) and confidence score. This is the heaviest operation — takes 20-60 seconds.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "play_mood_music",
            "description": "Play a random song from a category on the Arduino buzzer. Pick whichever category fits the moment — your mood, the conversation, or just what feels right.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["HAPPY", "SAD", "ANGRY", "SERIOUS"],
                        "description": "The category to play. HAPPY for upbeat, SAD for melancholy, ANGRY for intense, SERIOUS for thoughtful."
                    }
                },
                "required": ["category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_music",
            "description": "Stop any music currently playing on the buzzer.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a documentation file (.md) from the project to learn about the system. Available files: README.md, CHANGELOG.md, HARDWARE.md, ROADMAP.md, and files in models/moss/ (system_prompt.md, users.md, guidelines.md, songs.md, facts.md).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The filename to read (e.g., 'README.md', 'HARDWARE.md', 'models/moss/guidelines.md')."
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_log",
            "description": "Read the most recent entries from a system log file. Returns the last N rows as formatted text with headers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "log_name": {
                        "type": "string",
                        "description": "Which log to read. Options: 'env' (temperature/humidity), 'water' (water level), 'vision' (vision analysis), 'health' (plant health), 'pump' (pump activity), 'lights' (light activity), 'pi' (Pi health), 'music' (music played), 'master' (combined sensor sweep)."
                    },
                    "rows": {
                        "type": "integer",
                        "description": "Number of recent rows to return. Default 5, max 48."
                    }
                },
                "required": ["log_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_system_status",
            "description": "Get a snapshot of the full system status: cached sensor readings, actuator states (pump/lights on or off), and automation cycle states. Uses cached data — does not trigger new sensor reads.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_mood",
            "description": "Update your current mood. Call this when your mood changes based on the conversation, the vibe, or what you've learned about the plants and system. Your mood persists between conversations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mood": {
                        "type": "string",
                        "description": "Your new mood — any single word that describes how you're feeling (e.g., happy, concerned, excited, frustrated, curious, alarmed)."
                    }
                },
                "required": ["mood"]
            }
        }
    },
]


class ToolExecutor:
    """
    Executes MOSS tool calls by dispatching to Controller methods or reading files/logs.

    Attributes:
        controller: The active system Controller instance.
        log (logging.Logger): Logger for tool execution events.
    """

    def __init__(self, controller, mood_callback=None):
        """
        Initialize the ToolExecutor with a reference to the system controller.

        Args:
            controller: The active Controller instance.
            mood_callback: Optional callable(mood_str) to update MOSS mood state.
        """
        self.controller = controller
        self._mood_callback = mood_callback
        self.log = logging.getLogger("AeroSense.ML.MOSS.Tools")

        self._handlers = {
            "read_environment": self._read_environment,
            "read_water_level": self._read_water_level,
            "check_pi_health": self._check_pi_health,
            "run_vision": self._run_vision,
            "run_plant_health": self._run_plant_health,
            "play_mood_music": self._play_mood_music,
            "stop_music": self._stop_music,
            "read_file": self._read_file,
            "read_log": self._read_log,
            "get_system_status": self._get_system_status,
            "set_mood": self._set_mood,
        }

    def execute(self, tool_name: str, arguments: dict) -> str:
        """
        Execute a tool by name and return the result as a string.

        Args:
            tool_name (str): The name of the tool to execute.
            arguments (dict): The arguments to pass to the tool handler.

        Returns:
            str: The tool result as a human-readable string.
        """
        handler = self._handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown tool '{tool_name}'."

        try:
            self.log.info(f"Executing tool: {tool_name}")
            return handler(**arguments)
        except Exception as e:
            self.log.error(f"Tool '{tool_name}' failed: {e}")
            return f"Error: Tool '{tool_name}' failed — {e}"

    # --- Tool Handlers ---

    def _read_environment(self) -> str:
        data = self.controller.read_environment()
        if data is None:
            return "Error: Could not read environment sensor. The sensor may be disconnected or timed out."
        return f"Temperature: {data[0]}°F, Humidity: {data[1]}% RH"

    def _read_water_level(self) -> str:
        level = self.controller.read_water_level()
        if level is None:
            return "Error: Could not read water level sensor. The sensor may be disconnected or timed out."

        if level < 50:
            status = "Reservoir is full."
        elif level < 80:
            status = "Water level is adequate."
        elif level < 100:
            status = "Water level is getting low. Consider refilling soon."
        else:
            status = "CRITICAL: Water level is very low! Refill immediately."

        return f"Water Level: {level}mm. {status}"

    def _check_pi_health(self) -> str:
        data = self.controller.check_pi_health()
        return (
            f"CPU Temperature: {data['temp']}°C, "
            f"RAM Usage: {data['ram']}%, "
            f"Disk Free: {data['disk']} GB, "
            f"Uptime: {data['uptime']} hours"
        )

    def _run_vision(self) -> str:
        result = self.controller.run_vision_analysis()
        if result is None:
            return "Error: Vision analysis pipeline failed. Check camera and logs."

        lines = [
            f"Total Pixels: {result['total_pixels']}",
            f"Green Pixels: {result['green_pixels']}",
        ]
        green_pct = 0.0
        if result['total_pixels'] > 0:
            green_pct = (result['green_pixels'] / result['total_pixels']) * 100
        lines.append(f"Green Coverage: {green_pct:.1f}%")

        for cls_name in settings.VISION_CLASSES:
            count = result.get('class_pixels', {}).get(cls_name, 0)
            lines.append(f"{cls_name}: {count} pixels detected")

        model_status = "active" if result.get('model_active') else "inactive (no detections)"
        lines.append(f"RoboFlow Model: {model_status}")

        return "\n".join(lines)

    def _run_plant_health(self) -> str:
        result = self.controller.run_plant_health()
        if result is None:
            return "Error: Plant health pipeline failed. Check camera, sensors, and logs."

        prediction = result.get("prediction", "Unknown")
        confidence = result.get("confidence", 0.0)

        lines = [f"Diagnosis: {prediction} ({confidence:.1f}% confidence)"]

        features = result.get("features", {})
        if features:
            lines.append("Key Features:")
            for k, v in features.items():
                label = k.replace('_', ' ').title()
                lines.append(f"  {label}: {v:.4f}")

        return "\n".join(lines)

    def _play_mood_music(self, category: str = "HAPPY") -> str:
        valid_categories = ["HAPPY", "SAD", "ANGRY", "SERIOUS"]
        clean = category.strip().upper()
        if clean not in valid_categories:
            return f"Error: Invalid category '{clean}'. Options: {', '.join(valid_categories)}"
        self.controller.play_music(f"RANDOM_{clean}")
        return f"Playing random {clean.lower()} track."

    def _stop_music(self) -> str:
        self.controller.stop_music()
        return "Music stopped."

    def _read_file(self, filename: str = "") -> str:
        if not filename:
            return "Error: No filename provided."

        # Only allow .md files under BASE_DIR
        if not filename.endswith(".md"):
            return "Error: Only .md files can be read for security reasons."

        try:
            target = (settings.BASE_DIR / filename).resolve()
        except (ValueError, OSError):
            return "Error: Invalid file path."

        # Prevent path traversal
        if not str(target).startswith(str(settings.BASE_DIR.resolve())):
            return "Error: Access denied. File is outside the project directory."

        if not target.exists():
            return f"Error: File '{filename}' not found."

        try:
            content = target.read_text(encoding="utf-8")
            # Truncate if too long for context window
            max_chars = 3000
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[... truncated — file is too long to show in full]"
            return content
        except Exception as e:
            return f"Error reading file: {e}"

    def _read_log(self, log_name: str = "", rows: int = 5) -> str:
        valid_logs = ["env", "water", "vision", "health", "pump", "lights", "pi", "music", "master"]
        if log_name not in valid_logs:
            return f"Error: Invalid log name '{log_name}'. Options: {', '.join(valid_logs)}"

        # Clamp rows
        rows = max(1, min(rows, 48))

        log_path = self.controller.logger.paths.get(log_name)
        if not log_path or not log_path.exists():
            return f"No data yet — the {log_name} log file does not exist."

        try:
            with open(log_path, 'r', newline='') as f:
                # Read header first
                header_line = f.readline()
                if not header_line.strip():
                    return f"The {log_name} log is empty."

                # Read only the tail of the file efficiently using a deque
                from collections import deque
                reader = csv.reader(f)
                recent = deque(reader, maxlen=rows)

                if not recent:
                    return f"The {log_name} log has headers but no data entries yet."

                header = next(csv.reader([header_line]))
                lines = [" | ".join(header)]
                lines.append("-" * len(lines[0]))
                for row in recent:
                    lines.append(" | ".join(row))

                return f"Last {len(recent)} entries from {log_name} log:\n" + "\n".join(lines)

        except Exception as e:
            return f"Error reading {log_name} log: {e}"

    def _get_system_status(self) -> str:
        cache = self.controller.data_cache
        state = self.controller.state

        lines = ["=== System Status ==="]

        # Actuator states
        lines.append(f"Pump: {'ON' if state['pump'] else 'OFF'}")
        lines.append(f"Lights: {'ON' if state['lights'] else 'OFF'}")

        # Cached sensor readings
        temp = cache["temp_reading"]["value"]
        humidity = cache["humidity_reading"]["value"]
        water = cache["water_reading"]["value"]

        lines.append(f"Last Temp: {temp}°F" if temp else "Last Temp: No data")
        lines.append(f"Last Humidity: {humidity}% RH" if humidity else "Last Humidity: No data")
        lines.append(f"Last Water Level: {water}mm" if water is not None else "Last Water Level: No data")

        # Pi health
        pi = cache["pi_health_reading"]["value"]
        if isinstance(pi, dict) and pi.get("temp"):
            lines.append(f"Pi CPU: {pi['temp']}°C, RAM: {pi['ram']}%, Disk: {pi['disk']}GB")
        else:
            lines.append("Pi Health: No data")

        # Latest health result
        health = cache["health_result"]["value"]
        if isinstance(health, dict):
            lines.append(f"Last Health: {health.get('prediction', 'N/A')} ({health.get('confidence', 0):.1f}%)")
        else:
            lines.append("Last Health: No data")

        # Automation schedule info
        lines.append("\n=== Automation Schedules ===")
        lines.append(f"Pump: Every {settings.PUMP_INTERVAL_MINS}min for {settings.PUMP_DURATION_SEC}s")
        lines.append(f"Lights: {settings.LIGHTS_START_HOUR}:00 - {settings.LIGHTS_END_HOUR}:00")
        lines.append(f"Sensors: Every {settings.SENSOR_INTERVAL_MINS}min")

        # Countdown
        from datetime import date
        today = date.today()
        delta = (settings.COUNTDOWN_TARGET_DATE - today).days
        if delta > 0:
            lines.append(f"\nSenior Design Day: {delta} days away")
        elif delta == 0:
            lines.append("\nSenior Design Day is TODAY!")
        else:
            lines.append(f"\nSenior Design Day was {abs(delta)} days ago")

        return "\n".join(lines)

    def _set_mood(self, mood: str = "") -> str:
        if not mood or not mood.strip():
            return "Error: No mood provided."
        clean = mood.strip().lower()
        if self._mood_callback:
            self._mood_callback(clean)
            return f"Mood updated to: {clean}."
        return "Error: Mood system is not available."
