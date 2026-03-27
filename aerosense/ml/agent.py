"""
MOSS

This module implements the MossAgent class, the core AI agent for the AeroSense system.
It manages conversation state, keyword-based context injection, streaming responses,
and all interactions with the Ollama LLM backend.

Instead of LLM tool-calling, MOSS uses keyword detection to gather relevant data
BEFORE calling the LLM, then injects that data into the system prompt as context.
This eliminates the slow tool-calling round-trip loop.

Threading: The chat() method is designed to be called from a background thread.
A threading.Lock prevents concurrent inference. The main application loop is never blocked.
"""

import csv
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from config import settings


# Max age for archived conversation files (days)
ARCHIVE_MAX_AGE_DAYS: int = 7

# Max age (minutes) before stale data triggers a fresh reading
DATA_MAX_AGE_MINUTES: int = 30


class MossAgent:
    """
    The MOSS AI Agent — an Ollama-powered conversational assistant for AeroSense.

    Uses keyword-based context injection instead of LLM tool-calling.
    When keywords are detected in the user's message, relevant system data is
    gathered (from CSVs or live sensors) and injected into the system prompt.
    The LLM never calls tools directly.

    Attributes:
        controller: The active system Controller.
        scheduler: The active Scheduler (for cycle status).
        client: The Ollama client instance (lazy-loaded).
        conversation (list): The current message history.
        system_prompt (str): The loaded system prompt text.
        stats (dict): Usage statistics, persisted to disk.
        is_available (bool): Whether MOSS is ready to accept messages.
        is_busy (bool): Whether MOSS is currently processing a message.
        log (logging.Logger): Logger for MOSS events.
    """

    def __init__(self, controller, scheduler=None):
        """
        Initialize MossAgent. Does NOT load the model — call initialize() separately.

        Args:
            controller: The active Controller instance.
            scheduler: The active Scheduler instance (optional, for cycle status).
        """
        self.controller = controller
        self.scheduler = scheduler
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

    # --- Keyword Detection & Context Gathering ---

    # Maps keyword substrings to sets of context categories.
    # When a keyword is found in the user message, ALL categories in its set
    # are flagged for data gathering before the LLM call.
    KEYWORD_MAP = {
        # System / everything — triggers ALL categories
        "system":      {"health", "environment", "pump", "lights", "water_level"},
        "status":      {"health", "environment", "pump", "lights", "water_level"},
        "overview":    {"health", "environment", "pump", "lights", "water_level"},
        "everything":  {"health", "environment", "pump", "lights", "water_level"},
        "report":      {"health", "environment", "pump", "lights", "water_level"},
        # Cycle — triggers pump + lights
        "cycle":       {"pump", "lights"},
        "automat":     {"pump", "lights"},
        "schedule":    {"pump", "lights"},
        # Plant Health — also triggers environment (health depends on env data)
        "health":      {"health", "environment"},
        "plant":       {"health", "environment"},
        "diagnos":     {"health", "environment"},
        "sick":        {"health", "environment"},
        "dying":       {"health", "environment"},
        "dead":        {"health", "environment"},
        "yellow":      {"health"},
        "brown":       {"health"},
        "droop":       {"health"},
        "wilt":        {"health"},
        "chlorosis":   {"health"},
        "necrosis":    {"health"},
        "pest":        {"health"},
        "burn":        {"health"},
        "disease":     {"health"},
        "nutrient":    {"health"},
        "grow":        {"health"},
        "leaf":        {"health"},
        "leaves":      {"health"},
        # Environment — triggers env CSV check / fresh reading
        "temp":        {"environment"},
        "temperature": {"environment"},
        "humid":       {"environment"},
        "humidity":    {"environment"},
        "hot":         {"environment"},
        "cold":        {"environment"},
        "warm":        {"environment"},
        "cool":        {"environment"},
        "environment": {"environment"},
        "climate":     {"environment"},
        "air":         {"environment"},
        "vpd":         {"environment"},
        # Pump — triggers pump/cycle status check
        "pump":        {"pump"},
        "irrigat":     {"pump"},
        "spray":       {"pump"},
        "mist":        {"pump"},
        # Water Level — triggers water level sensor check
        "water":       {"pump", "water_level"},
        "watering":    {"pump"},
        "reservoir":   {"water_level"},
        "level":       {"water_level"},
        "refill":      {"water_level"},
        "empty":       {"water_level"},
        "fill":        {"water_level"},
        # Lights — triggers light/cycle status check
        "light":       {"lights"},
        "lights":      {"lights"},
        "lamp":        {"lights"},
        "led":         {"lights"},
        "bright":      {"lights"},
        "dark":        {"lights"},
    }

    def _detect_keywords(self, message: str) -> set:
        """
        Scan user message for keywords and return the set of matched context categories.

        Args:
            message: The user's message text.

        Returns:
            Set of category strings (e.g., {"health", "pump", "water_level"}).
        """
        lower = message.lower()
        categories = set()
        for keyword, cats in self.KEYWORD_MAP.items():
            if keyword in lower:
                categories.update(cats)
        return categories

    def _gather_context(self, categories: set, stream_callback: Optional[Callable] = None) -> str:
        """
        Gather system data for the matched keyword categories.

        For health and environment, checks CSV freshness. If data is older than
        DATA_MAX_AGE_MINUTES, takes a fresh reading (which may take time for health).

        Args:
            categories: Set of context categories to gather.
            stream_callback: Optional callback to show progress to user.

        Returns:
            str: Formatted context block to inject into the system prompt.
        """
        context_parts = []

        if "health" in categories:
            context_parts.append(self._gather_health_context(stream_callback))

        if "environment" in categories:
            context_parts.append(self._gather_env_context(stream_callback))

        if "pump" in categories:
            context_parts.append(self._gather_pump_context())

        if "lights" in categories:
            context_parts.append(self._gather_lights_context())

        if "water_level" in categories:
            context_parts.append(self._gather_water_level_context(stream_callback))

        if not context_parts:
            return ""

        return "\n[SENSOR DATA]\n" + "\n".join(context_parts)

    def _gather_health_context(self, stream_callback: Optional[Callable] = None) -> str:
        """Gather plant health data. Checks CSV freshness, takes fresh reading if stale."""
        log_path = settings.LOG_DIR / "health_log.csv"
        last_entry = self._read_csv_last_row(log_path)

        minutes_ago = None
        data_fresh = False

        if last_entry:
            try:
                ts = datetime.strptime(last_entry[0], "%Y-%m-%d %H:%M:%S")
                minutes_ago = (datetime.now() - ts).total_seconds() / 60.0
                data_fresh = minutes_ago <= DATA_MAX_AGE_MINUTES
            except (ValueError, IndexError):
                pass

        if data_fresh and last_entry:
            self.log.info(f"Health data is fresh ({minutes_ago:.0f} min old). Using CSV.")
            return self._format_health_from_csv(last_entry, minutes_ago)

        # Stale or missing — take a fresh reading
        self.log.info("Health data is stale or missing. Running fresh plant health...")
        if stream_callback:
            try:
                stream_callback("[gathering plant health data...] ")
            except Exception:
                pass

        result = self.controller.run_plant_health()
        if result is None:
            return "HEALTH: unavailable (sensor error)"

        prediction = result.get("prediction", "Unknown")
        confidence = result.get("confidence", 0.0)
        features = result.get("features", {})

        parts = [f"HEALTH (fresh): {prediction}, {confidence:.1f}% conf"]
        vision_map = {"chlorosis_ratio": "chlorosis", "decay_ratio": "decay",
                      "tip_burn_ratio": "tip_burn", "pest_density": "pest", "wilting_ratio": "wilting"}
        ratios = [f"{v}={features[k] * 100:.2f}%" for k, v in vision_map.items() if k in features]
        if ratios:
            parts.append(" | " + ", ".join(ratios))

        return "".join(parts)

    def _gather_env_context(self, stream_callback: Optional[Callable] = None) -> str:
        """Gather environment data. Checks CSV freshness, takes fresh reading if stale."""
        log_path = settings.LOG_DIR / "env_log.csv"
        last_entry = self._read_csv_last_row(log_path)

        minutes_ago = None
        data_fresh = False

        if last_entry:
            try:
                ts = datetime.strptime(last_entry[0], "%Y-%m-%d %H:%M:%S")
                minutes_ago = (datetime.now() - ts).total_seconds() / 60.0
                data_fresh = minutes_ago <= DATA_MAX_AGE_MINUTES
            except (ValueError, IndexError):
                pass

        if data_fresh and last_entry:
            self.log.info(f"Env data is fresh ({minutes_ago:.0f} min old). Using CSV.")
            try:
                temp_f = float(last_entry[1])
                humidity = float(last_entry[2])
                return f"ENV ({minutes_ago:.0f}min ago): {temp_f:.1f}°F, {humidity:.1f}% RH"
            except (ValueError, IndexError):
                pass

        # Stale or missing — take a fresh reading
        self.log.info("Env data is stale or missing. Reading environment sensors...")
        if stream_callback:
            try:
                stream_callback("[reading environment sensors...] ")
            except Exception:
                pass

        env = self.controller.read_environment()
        if env is None:
            return "ENV: unavailable (sensor error)"

        return f"ENV (fresh): {env[0]:.1f}°F, {env[1]:.1f}% RH"

    def _gather_pump_context(self) -> str:
        """Gather pump hardware state and automation cycle status."""
        pump_on = self.controller.state.get("pump", False)
        if pump_on:
            elapsed = time.time() - self.controller.state.get("pump_start_time", 0)
            expected = self.controller.state.get("pump_expected_duration", 0)
            remaining = max(0, expected - elapsed)
            hw = f"ON ({elapsed:.0f}s elapsed, ~{remaining:.0f}s left)"
        else:
            hw = "OFF"

        cycle = "unknown"
        if self.scheduler:
            cycle = "ENABLED" if self.scheduler.cycles.get("pump", False) else "DISABLED"

        schedule = f"every {settings.PUMP_INTERVAL_MINS}min for {settings.PUMP_DURATION_SEC}s"
        return f"PUMP: {hw} | cycle: {cycle} | schedule: {schedule}"

    def _gather_lights_context(self) -> str:
        """Gather lights hardware state and automation cycle status."""
        lights_on = self.controller.state.get("lights", False)
        if lights_on:
            elapsed = time.time() - self.controller.state.get("lights_start_time", 0)
            expected = self.controller.state.get("lights_expected_duration", 0)
            remaining = max(0, expected - elapsed)
            hw = f"ON ({elapsed:.0f}s elapsed, ~{remaining:.0f}s left)"
        else:
            hw = "OFF"

        cycle = "unknown"
        if self.scheduler:
            cycle = "ENABLED" if self.scheduler.cycles.get("lights", False) else "DISABLED"

        schedule = f"{settings.LIGHTS_START_HOUR}:00-{settings.LIGHTS_END_HOUR}:00"
        return f"LIGHTS: {hw} | cycle: {cycle} | schedule: {schedule}"

    def _gather_water_level_context(self, stream_callback: Optional[Callable] = None) -> str:
        """Gather water level data. Checks CSV freshness, takes fresh reading if stale."""
        log_path = settings.LOG_DIR / "water_log.csv"
        last_entry = self._read_csv_last_row(log_path)

        minutes_ago = None
        data_fresh = False

        if last_entry:
            try:
                ts = datetime.strptime(last_entry[0], "%Y-%m-%d %H:%M:%S")
                minutes_ago = (datetime.now() - ts).total_seconds() / 60.0
                data_fresh = minutes_ago <= DATA_MAX_AGE_MINUTES
            except (ValueError, IndexError):
                pass

        level_mm = None

        if data_fresh and last_entry:
            self.log.info(f"Water level data is fresh ({minutes_ago:.0f} min old). Using CSV.")
            try:
                level_mm = int(last_entry[1])
            except (ValueError, IndexError):
                pass
        else:
            self.log.info("Water level data is stale or missing. Reading sensor...")
            if stream_callback:
                try:
                    stream_callback("[reading water level...] ")
                except Exception:
                    pass
            level_mm = self.controller.read_water_level()
            minutes_ago = 0

        if level_mm is None:
            return "WATER: unavailable (sensor error)"

        # Determine status
        if level_mm <= 80:
            status = "healthy"
        elif level_mm <= 100:
            status = "medium, refill soon"
        else:
            status = "LOW/CRITICAL, pump may not run"

        age = "fresh" if minutes_ago is not None and minutes_ago < 1 else f"{minutes_ago:.0f}min ago"
        return f"WATER ({age}): {level_mm}mm — {status}"

    def _format_health_from_csv(self, row: list, minutes_ago: float) -> str:
        """Format a compact health context string from a CSV row."""
        try:
            prediction = row[17]
            confidence = float(row[18])
            chlorosis = float(row[1]) * 100
            decay = float(row[2]) * 100
            tip_burn = float(row[3]) * 100
            pest = float(row[4]) * 100
            wilting = float(row[5]) * 100

            return (f"HEALTH ({minutes_ago:.0f}min ago): {prediction}, {confidence:.1f}% conf"
                    f" | chlorosis={chlorosis:.2f}%, decay={decay:.2f}%, tip_burn={tip_burn:.2f}%,"
                    f" pest={pest:.2f}%, wilting={wilting:.2f}%")
        except (IndexError, ValueError) as e:
            self.log.warning(f"Failed to parse health CSV row: {e}")
            return "HEALTH: data exists but could not be parsed"

    def _read_csv_last_row(self, path: Path) -> Optional[list]:
        """
        Read the last data row from a CSV file (skipping header).

        Args:
            path: Path to the CSV file.

        Returns:
            The last row as a list of strings, or None if empty/missing.
        """
        if not path.exists():
            return None

        try:
            with open(path, "r", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header
                last = None
                for row in reader:
                    if row:
                        last = row
                return last
        except Exception:
            return None

    # --- Chat ---

    def chat(self, message: str, stream_callback: Optional[Callable[[str], None]] = None) -> str:
        """
        Send a message to MOSS and get a response.

        This method handles the full conversation loop: detect keywords, gather context,
        inject it into the system prompt, call the LLM (with streaming), and return
        the final response text. No tool-calling is involved.

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

        Flow:
            1. Detect keywords in user message
            2. Gather relevant context (may take time for health readings)
            3. Build system message with injected context
            4. Call Ollama once (no tool loop)
            5. Return response

        Args:
            message (str): User message.
            stream_callback (Optional[Callable]): Token streaming callback.

        Returns:
            str: Complete response text.
        """
        # Step 1: Detect keywords
        categories = self._detect_keywords(message)
        if categories:
            self.log.info(f"Keywords detected — gathering context for: {categories}")
        else:
            self.log.info("No keywords detected — pure conversational response.")

        # Step 2: Gather context (may take time if readings are stale)
        injected_context = self._gather_context(categories, stream_callback)

        # Step 3: Build system message with context
        system_msg = self._build_system_message(injected_context)

        # Append user message to conversation
        self.conversation.append({"role": "user", "content": message})

        # Trim conversation if too long
        self._trim_conversation()

        # Build messages for the API call
        messages = [{"role": "system", "content": system_msg}] + self.conversation

        # Step 4: Call Ollama (single call, no tool loop)
        response_text = self._call_ollama(messages, stream_callback)

        # Handle empty response
        if not response_text or not response_text.strip():
            response_text = "I'm not sure how to respond to that. Could you rephrase?"
            self.log.warning("Model returned empty response.")

        # Append assistant response to conversation
        self.conversation.append({"role": "assistant", "content": response_text})

        # Update stats
        self.stats["total_messages"] += 1
        self.stats["last_active"] = datetime.now().isoformat()
        self._save_stats()

        # Auto-save conversation
        self._save_conversation()

        return response_text

    def _call_ollama(self, messages: List[Dict], stream_callback: Optional[Callable]) -> str:
        """
        Make a single call to Ollama's chat API with optional streaming.
        No tools are sent — pure LLM inference.

        Args:
            messages (list): The full message list to send.
            stream_callback (Optional[Callable]): Token callback for streaming.

        Returns:
            str: The response text.
        """
        kwargs = {
            "model": settings.MOSS_MODEL,
            "messages": messages,
            "options": {"num_ctx": settings.MOSS_CONTEXT_LENGTH},
            "keep_alive": settings.MOSS_KEEP_ALIVE,
        }

        if stream_callback:
            # Streaming mode
            response_text = ""

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

            return response_text
        else:
            # Non-streaming mode
            response = self.client.chat(**kwargs)
            msg = getattr(response, "message", None) or (response.get("message", {}) if isinstance(response, dict) else {})
            response_text = getattr(msg, "content", None) or (msg.get("content", "") if isinstance(msg, dict) else "")
            return response_text

    def _build_system_message(self, injected_context: str = "") -> str:
        """
        Build the full system message: base prompt + reference docs + injected context + time.

        Args:
            injected_context: Pre-gathered context string to inject (may be empty).

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

        # Inject gathered context (health, environment, pump, lights)
        if injected_context:
            parts.append(injected_context)

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
