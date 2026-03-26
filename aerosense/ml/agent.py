"""
MOSS

This module implements the MossAgent class, the core AI agent for the AeroSense system.
It manages conversation state, tool calling, streaming responses,
and all interactions with the Ollama LLM backend.

Threading: The chat() method is designed to be called from a background thread.
A threading.Lock prevents concurrent inference. The main application loop is never blocked.
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

from aerosense.ml.tools import TOOL_SCHEMAS, ToolExecutor
from config import settings


# Max age for archived conversation files (days)
ARCHIVE_MAX_AGE_DAYS: int = 7


class MossAgent:
    """
    The MOSS AI Agent — an Ollama-powered conversational assistant for AeroSense.

    Attributes:
        controller: The active system Controller.
        tool_executor (ToolExecutor): Dispatches tool calls to Controller methods.
        client: The Ollama client instance (lazy-loaded).
        conversation (list): The current message history.
        system_prompt (str): The loaded system prompt text.
        stats (dict): Usage statistics, persisted to disk.
        is_available (bool): Whether MOSS is ready to accept messages.
        is_busy (bool): Whether MOSS is currently processing a message.
        log (logging.Logger): Logger for MOSS events.
    """

    def __init__(self, controller):
        """
        Initialize MossAgent. Does NOT load the model — call initialize() separately.

        Args:
            controller: The active Controller instance.
        """
        self.controller = controller
        self.tool_executor = ToolExecutor(controller)
        self.client = None
        self.conversation: List[Dict] = []
        self.system_prompt: str = ""
        self.stats: Dict = {"total_messages": 0, "total_tool_calls": 0, "total_conversations": 0, "total_resets": 0, "first_boot": None, "last_active": None}
        self.is_available: bool = False
        self.is_busy: bool = False
        self._loading: bool = False
        self._initialized: bool = False
        self._lock = threading.Lock()
        self.log = logging.getLogger("AeroSense.ML.MOSS")

    # --- Initialization ---

    def initialize(self):
        """
        Lazy-load MOSS: import ollama, ping server, ensure model is pulled,
        load system prompt and persisted state.

        Designed to run in a background thread so it doesn't block system boot.
        Sets is_available=True on success, False on any failure.
        Guards against double initialization.
        """
        # Prevent double init
        if self._initialized or self._loading:
            self.log.warning("MOSS initialize() called again — skipping.")
            return

        self._loading = True
        self.log.info("MOSS initializing...")

        try:
            import ollama
        except ImportError:
            self.log.error("MOSS unavailable: 'ollama' package not installed. Run: pip install ollama")
            self._loading = False
            return

        # Connect to Ollama server
        try:
            self.client = ollama.Client(host=settings.MOSS_HOST)
            self.client.list()
            self.log.info(f"Connected to Ollama at {settings.MOSS_HOST}")
        except Exception as e:
            self.log.error(f"MOSS unavailable: Cannot connect to Ollama at {settings.MOSS_HOST} — {e}")
            self.log.error("Ensure Ollama is running: 'ollama serve'")
            self.client = None
            self._loading = False
            return

        # Ensure model is pulled
        try:
            models = self.client.list()
            model_names = [m.model for m in models.models] if hasattr(models, 'models') else []

            # Check if our model is available
            found = any(settings.MOSS_MODEL in name for name in model_names)
            if not found:
                self.log.info(f"Model '{settings.MOSS_MODEL}' not found locally. Pulling (this may take a few minutes)...")
                self.client.pull(settings.MOSS_MODEL)
                self.log.info(f"Model '{settings.MOSS_MODEL}' pulled successfully.")
            else:
                self.log.info(f"Model '{settings.MOSS_MODEL}' is available.")
        except Exception as e:
            self.log.error(f"MOSS unavailable: Failed to verify/pull model '{settings.MOSS_MODEL}' — {e}")
            self.client = None
            self._loading = False
            return

        # Load system prompt
        self._load_system_prompt()

        # Load persisted state
        self._load_stats()

        # Reset conversation on boot for a clean context
        self.reset()

        # Clean up old archived conversations
        self._cleanup_archives()

        # Record first boot
        if not self.stats["first_boot"]:
            self.stats["first_boot"] = datetime.now().isoformat()
        self.stats["total_conversations"] += 1
        self._save_stats()

        self._initialized = True
        self.is_available = True
        self._loading = False
        self.log.info("MOSS is ready.")

    # --- Tool Gating ---

    # Maps keywords (substring matched) to the tool names they should activate.
    # A keyword can activate multiple tools. Only matched tools are sent to the model.
    TOOL_KEYWORD_MAP = {
        # run_plant_health
        "health":      {"run_plant_health"},
        "diagnos":     {"run_plant_health"},
        "sick":        {"run_plant_health"},
        "dying":       {"run_plant_health"},
        "dead":        {"run_plant_health"},
        "yellow":      {"run_plant_health"},
        "brown":       {"run_plant_health"},
        "droop":       {"run_plant_health"},
        "wilt":        {"run_plant_health"},
        "chlorosis":   {"run_plant_health"},
        "necrosis":    {"run_plant_health"},
        "pest":        {"run_plant_health"},
        "burn":        {"run_plant_health"},
        "disease":     {"run_plant_health"},
        "nutrient":    {"run_plant_health"},
        "run":         {"run_plant_health"},
    }

    # Build a name→schema lookup from TOOL_SCHEMAS for fast filtering
    _SCHEMA_BY_NAME = {s["function"]["name"]: s for s in TOOL_SCHEMAS}

    def _get_relevant_tools(self, message: str) -> list:
        """
        Determine which tool schemas to send based on keywords in the message.
        Returns a filtered list of tool schemas, or an empty list if no keywords match.
        """
        lower = message.lower()
        matched_names = set()
        for keyword, tool_names in self.TOOL_KEYWORD_MAP.items():
            if keyword in lower:
                matched_names.update(tool_names)

        if not matched_names:
            return []

        return [self._SCHEMA_BY_NAME[name] for name in matched_names if name in self._SCHEMA_BY_NAME]

    # --- Chat ---

    def chat(self, message: str, stream_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Send a message to MOSS and get a response.

        This method handles the full conversation loop: append user message, call the LLM
        (with streaming), handle tool calls, and return the final response text.

        Thread-safe: acquires _lock so only one inference runs at a time.
        If MOSS is already busy, returns a "busy" message immediately.

        Args:
            message (str): The user's message text.
            stream_callback (Optional[Callable]): Called with each token as it's generated.
                If None, tokens are collected silently.

        Returns:
            str: The complete response text from MOSS.
        """
        if not self.is_available or not self.client:
            return "MOSS is not available right now."

        # Non-blocking busy check: if already processing, reject immediately
        if not self._lock.acquire(blocking=False):
            return "I'm still thinking about the last message. Please wait a moment."

        try:
            self.is_busy = True
            return self._run_chat(message, stream_callback)
        except Exception as e:
            self.log.error(f"Chat error: {e}")
            self._check_connection()
            return f"I encountered an error: {e}"
        finally:
            self.is_busy = False
            self._lock.release()

    def _run_chat(self, message: str, stream_callback: Optional[Callable]) -> str:
        """
        Internal chat implementation. Assumes _lock is held.

        Args:
            message (str): User message.
            stream_callback (Optional[Callable]): Token streaming callback.

        Returns:
            str: Complete response text.
        """
        # Build the system message
        system_msg = self._build_system_message()

        # Append user message
        self.conversation.append({"role": "user", "content": message})

        # Trim conversation if too long
        self._trim_conversation()

        # Build messages for the API call
        messages = [{"role": "system", "content": system_msg}] + self.conversation

        # Determine which tools (if any) are relevant to this message
        relevant_tools = self._get_relevant_tools(message)
        if relevant_tools:
            tool_names = [t["function"]["name"] for t in relevant_tools]
            self.log.info(f"Sending {len(relevant_tools)} tool(s): {tool_names}")
        else:
            self.log.info("No tool keywords detected — skipping tool schemas.")

        # Tool calling loop
        tool_calls_made = 0
        full_response = ""
        streamed_any_text = False
        used_tools = False

        while True:
            # Call Ollama with streaming
            response_text, tool_calls = self._call_ollama(messages, stream_callback, tools=relevant_tools)

            if response_text.strip():
                streamed_any_text = True

            if not tool_calls:
                # No tool calls — we have the final response
                full_response = response_text
                break

            # Process tool calls (up to safety cap)
            if tool_calls_made >= settings.MOSS_MAX_TOOLS_PER_TURN:
                self.log.warning(f"Tool call cap reached ({settings.MOSS_MAX_TOOLS_PER_TURN}). Forcing final response.")
                messages.append({"role": "assistant", "content": response_text})
                messages.append({"role": "user", "content": "[System: Tool call limit reached. Please provide your final response based on the information you have.]"})
                response_text, _ = self._call_ollama(messages, stream_callback, tools=[])
                full_response = response_text
                break

            # Execute each tool call — mark that we entered a tool loop
            used_tools = True
            messages.append({"role": "assistant", "content": response_text, "tool_calls": tool_calls})

            for tc in tool_calls:
                # Enforce cap per individual tool call, not just per loop iteration
                if tool_calls_made >= settings.MOSS_MAX_TOOLS_PER_TURN:
                    self.log.warning(f"Tool call cap reached mid-batch. Skipping remaining tool calls.")
                    break

                # Safely extract function info — support both dict and object tool calls
                if isinstance(tc, dict):
                    func = tc.get("function", {})
                    tool_name = func.get("name", "unknown")
                    tool_args = func.get("arguments", {})
                else:
                    func = getattr(tc, "function", None)
                    tool_name = getattr(func, "name", "unknown") if func else "unknown"
                    tool_args = getattr(func, "arguments", {}) if func else {}

                # Handle string arguments (some models return JSON string)
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}

                # Ensure tool_args is a dict
                if not isinstance(tool_args, dict):
                    tool_args = {}

                self.log.info(f"Tool call: {tool_name}({tool_args})")

                # Show tool activity feedback to user via stream callback
                if stream_callback and not streamed_any_text:
                    try:
                        stream_callback(f"[checking {tool_name}...] ")
                    except Exception:
                        pass

                result = self.tool_executor.execute(tool_name, tool_args)
                tool_calls_made += 1

                messages.append({
                    "role": "tool",
                    "content": result,
                })

                self.stats["total_tool_calls"] += 1

        # Handle empty response
        if not full_response or not full_response.strip():
            full_response = "I'm not sure how to respond to that. Could you rephrase?"
            self.log.warning("Model returned empty response.")

        # Append assistant response to conversation
        self.conversation.append({"role": "assistant", "content": full_response})

        # Update stats
        self.stats["total_messages"] += 1
        self.stats["last_active"] = datetime.now().isoformat()
        self._save_stats()

        # Auto-save conversation
        self._save_conversation()

        return full_response

    def _call_ollama(self, messages: List[Dict], stream_callback: Optional[Callable], tools: Optional[list] = None):
        """
        Make a single call to Ollama's chat API with optional streaming.

        Args:
            messages (list): The full message list to send.
            stream_callback (Optional[Callable]): Token callback for streaming.
            tools (Optional[list]): Tool schemas to include. Empty list or None = no tools.

        Returns:
            Tuple[str, list]: (response_text, tool_calls). tool_calls is empty if none were made.
        """
        kwargs = {
            "model": settings.MOSS_MODEL,
            "messages": messages,
            "options": {"num_ctx": settings.MOSS_CONTEXT_LENGTH},
            "keep_alive": settings.MOSS_KEEP_ALIVE,
        }

        if tools:
            kwargs["tools"] = tools

        if stream_callback:
            # Streaming mode
            response_text = ""
            tool_calls = []

            stream = self.client.chat(**kwargs, stream=True)
            for chunk in stream:
                # Support both object attributes and dict access
                msg = getattr(chunk, "message", None) or (chunk.get("message", {}) if isinstance(chunk, dict) else {})

                # Collect streamed text
                token = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
                if token:
                    response_text += token
                    try:
                        stream_callback(token)
                    except Exception as cb_err:
                        self.log.warning(f"Stream callback error (non-fatal): {cb_err}")

                # Collect tool calls (usually in the last chunk)
                tc = getattr(msg, "tool_calls", None) or (msg.get("tool_calls") if isinstance(msg, dict) else None)
                if tc and isinstance(tc, list):
                    tool_calls.extend(tc)

            return response_text, tool_calls
        else:
            # Non-streaming mode
            response = self.client.chat(**kwargs)
            msg = getattr(response, "message", None) or (response.get("message", {}) if isinstance(response, dict) else {})
            response_text = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            tool_calls = getattr(msg, "tool_calls", None) or (msg.get("tool_calls", []) if isinstance(msg, dict) else [])
            if not isinstance(tool_calls, list):
                tool_calls = []
            return response_text, tool_calls

    def _build_system_message(self) -> str:
        """
        Build the full system message: base prompt + reference docs + dynamic state (time).

        Returns:
            str: The complete system prompt string.
        """
        parts = [self.system_prompt]

        # Inject reference docs (overview + guidelines)
        for filename in ("overview.md", "guidelines.md"):
            path = settings.MOSS_MODEL_FILES_DIR / filename
            try:
                if path.exists():
                    parts.append(path.read_text(encoding="utf-8"))
            except IOError:
                pass

        # Inject live sensor data
        sensor_line = "\n## Live Sensor Data (do NOT mention unless the user asks)"
        try:
            env = self.controller.read_environment()
            if env:
                sensor_line += f"\n- Temperature: {env[0]}°F, Humidity: {env[1]}% RH"
            else:
                sensor_line += "\n- Environment sensor: unavailable"
        except Exception:
            sensor_line += "\n- Environment sensor: error"
        try:
            level = self.controller.read_water_level()
            if level is not None:
                sensor_line += f"\n- Water Level: {level}mm"
            else:
                sensor_line += "\n- Water level sensor: unavailable"
        except Exception:
            sensor_line += "\n- Water level sensor: error"
        parts.append(sensor_line)

        # Inject current date/time
        now = datetime.now()
        parts.append(f"\nCurrent date and time: {now.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(parts)

    # --- Conversation Management ---

    def reset(self):
        """
        Reset the conversation. Saves the current conversation to an archive file first,
        then clears the active conversation and deletes the active file.
        """
        if self.conversation:
            self._save_conversation(archive=True)

        self.conversation = []
        self.stats["total_resets"] += 1
        self._save_stats()

        # Delete the active conversation file
        active_path = settings.MOSS_CONVERSATION_DIR / "active_conversation.json"
        try:
            if active_path.exists():
                active_path.unlink()
        except OSError as e:
            self.log.warning(f"Failed to delete active conversation file: {e}")

        self.log.info("Conversation reset.")

    def _trim_conversation(self):
        """
        Trim conversation history to stay within context limits.
        Keeps the most recent messages, dropping the oldest (excluding system prompt).
        """
        max_messages = settings.MOSS_MAX_CONVERSATION_MESSAGES
        if len(self.conversation) > max_messages:
            trimmed_count = len(self.conversation) - max_messages
            self.conversation = self.conversation[-max_messages:]
            self.log.info(f"Conversation trimmed: removed {trimmed_count} oldest messages.")

    def _save_conversation(self, archive: bool = False):
        """
        Save the current conversation to disk.

        Args:
            archive (bool): If True, save to a timestamped archive file instead of the active file.
        """
        try:
            if archive:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                path = settings.MOSS_CONVERSATION_DIR / f"conversation_{timestamp}.json"
            else:
                path = settings.MOSS_CONVERSATION_DIR / "active_conversation.json"

            data = {
                "saved_at": datetime.now().isoformat(),
                "message_count": len(self.conversation),
                "messages": self.conversation
            }

            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            self.log.error(f"Failed to save conversation: {e}")

    def _load_conversation(self):
        """Load the active conversation from disk if it exists."""
        path = settings.MOSS_CONVERSATION_DIR / "active_conversation.json"
        if not path.exists():
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            messages = data.get("messages", [])

            # Validate that messages are well-formed
            valid = []
            for msg in messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    valid.append(msg)

            self.conversation = valid
            if valid:
                self.log.info(f"Resumed conversation with {len(valid)} messages.")
        except (json.JSONDecodeError, KeyError, IOError) as e:
            self.log.warning(f"Failed to load conversation (starting fresh): {e}")
            self.conversation = []

    def _cleanup_archives(self):
        """
        Delete archived conversation files older than ARCHIVE_MAX_AGE_DAYS.
        Prevents unbounded disk growth over months of operation.
        """
        try:
            cutoff = time.time() - (ARCHIVE_MAX_AGE_DAYS * 86400)
            cleaned = 0

            for f in settings.MOSS_CONVERSATION_DIR.glob("conversation_*.json"):
                if f.stat().st_mtime < cutoff:
                    f.unlink()
                    cleaned += 1

            if cleaned > 0:
                self.log.info(f"Cleaned up {cleaned} archived conversation(s) older than {ARCHIVE_MAX_AGE_DAYS} days.")
        except Exception as e:
            self.log.warning(f"Archive cleanup failed (non-fatal): {e}")

    # --- Stats ---

    def _load_stats(self):
        """Load usage stats from disk."""
        try:
            if settings.MOSS_STATS_PATH.exists():
                data = json.loads(settings.MOSS_STATS_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict) and "total_messages" in data:
                    self.stats = data
        except (json.JSONDecodeError, IOError) as e:
            self.log.warning(f"Failed to load stats (using default): {e}")

    def _save_stats(self):
        """Persist usage stats to disk."""
        try:
            settings.MOSS_STATS_PATH.write_text(json.dumps(self.stats, indent=2), encoding="utf-8")
        except IOError as e:
            self.log.error(f"Failed to save stats: {e}")

    # --- System Prompt ---

    def _load_system_prompt(self):
        """Load the system prompt from the model files directory."""
        prompt_path = settings.MOSS_MODEL_FILES_DIR / "system_prompt.md"
        try:
            if prompt_path.exists():
                self.system_prompt = prompt_path.read_text(encoding="utf-8")
                self.log.info("System prompt loaded.")
            else:
                self.log.warning("System prompt file not found. Using fallback.")
                self.system_prompt = "You are MOSS, the AI assistant for the AeroSense garden system. Be helpful and concise."
        except IOError as e:
            self.log.error(f"Failed to load system prompt: {e}")
            self.system_prompt = "You are MOSS, the AI assistant for the AeroSense garden system. Be helpful and concise."

    # --- Connection Health ---

    def _check_connection(self):
        """Check if Ollama is still reachable. Mark unavailable if not."""
        try:
            if self.client:
                self.client.list()
        except Exception:
            self.log.error("Lost connection to Ollama. MOSS is now unavailable.")
            self.is_available = False

    # --- Shutdown ---

    def shutdown(self):
        """
        Save state before system shutdown.
        Acquires the lock to ensure no chat is in progress during save.
        Uses a timeout to avoid blocking shutdown indefinitely.
        """
        self.log.info("MOSS shutting down. Saving state...")

        # Try to acquire lock with timeout
        acquired = self._lock.acquire(timeout=5.0)
        try:
            if self.conversation:
                self._save_conversation()
            self._save_stats()
            self.log.info("MOSS state saved.")
        finally:
            if acquired:
                self._lock.release()
