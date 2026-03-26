"""
MOSS Tool Definitions.

This module defines the tools available to the MOSS AI agent.
Each tool has an Ollama-compatible schema and a handler function
that wraps existing Controller methods or reads system data.
"""

import inspect
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
            "description": "Read live temperature (°F) and humidity (% RH) from sensors.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_water_level",
            "description": "Read live water level (mm). Lower = more water. Over 100mm = critical.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_plant_health",
            "description": "Run plant health classifier. Returns health class and confidence. Takes 20-60 seconds.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a reference file: 'overview.md' (system info) or 'guidelines.md' (plant care).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "'overview.md' or 'guidelines.md'"
                    }
                },
                "required": ["filename"]
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

    def __init__(self, controller):
        """
        Initialize the ToolExecutor with a reference to the system controller.

        Args:
            controller: The active Controller instance.
        """
        self.controller = controller
        self.log = logging.getLogger("AeroSense.ML.MOSS.Tools")

        self._handlers = {
            "read_environment": self._read_environment,
            "read_water_level": self._read_water_level,
            "run_plant_health": self._run_plant_health,
            "read_file": self._read_file,
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
            # Strip bogus arguments for parameterless tools
            sig = inspect.signature(handler)
            if not sig.parameters:
                return handler()
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

    def _read_file(self, filename: str = "") -> str:
        if not filename:
            return "Error: No filename provided."

        # Only allow .md files under the moss model files directory
        if not filename.endswith(".md"):
            return "Error: Only .md files can be read."

        # Restrict to models/moss/ directory only
        allowed_files = ["overview.md", "guidelines.md"]
        clean_name = Path(filename).name
        if clean_name not in allowed_files:
            return f"Error: File not available. Allowed files: {', '.join(allowed_files)}"

        try:
            target = (settings.MOSS_MODEL_FILES_DIR / clean_name).resolve()
        except (ValueError, OSError):
            return "Error: Invalid file path."

        if not target.exists():
            return f"Error: File '{clean_name}' not found."

        try:
            content = target.read_text(encoding="utf-8")
            # Truncate if too long for context window
            max_chars = 2000
            if len(content) > max_chars:
                content = content[:max_chars] + "\n\n[... truncated]"
            return content
        except Exception as e:
            return f"Error reading file: {e}"

