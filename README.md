# AeroSense
**Version: v5.17.3** | **Release: 2026-04-15**

Aeroponics is one of the most efficient ways to grow plants, using up to 90% less water than soil while producing faster growth. But most aeroponic systems on the market are industrial grade, expensive, and require a lot of background knowledge to run. They're not built for everyday people. **AeroSense** was built to change that. It's a smart controller that automates the hard parts so anyone can grow, regardless of experience.

This is a Senior Design capstone project built from scratch by a team of engineering students at the **University of Akron**. The platform runs on a **dual-processor architecture** where a **Raspberry Pi 5** handles all the high-level logic in Python while an **Arduino Mega 2560** runs the real-time firmware in C++. Together they manage everything from sensor reading and hardware control to machine learning and a full web dashboard.

At its core, AeroSense follows a **Sense → Analyze → Act** pipeline. Sensors and a camera collect data, three ML systems analyze it (computer vision for disease detection, a health classifier for diagnosis, and an AI assistant for recommendations), and the user acts on those insights to tune the system. It's a decision-support tool, not a black box.

---

## Table of Contents
1. [Documentation](#documentation)
2. [Directory Structure](#directory-structure)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
5. [System Usage](#system-usage)
6. [System Architecture](#system-architecture)
7. [Data Systems](#data-systems)
8. [Machine Learning](#machine-learning)
9. [Configuration Reference](#configuration-reference)
10. [Shutdown Procedure](#shutdown-procedure)

---

## Documentation
* **[CHANGELOG.md](CHANGELOG.md):** Version history and release notes.
* **[HARDWARE.md](HARDWARE.md):** Wiring schematics, pinouts, and power distribution.
* **[README.md](README.md):** Project overview, installation, and operational manual.
* **[ROADMAP.md](ROADMAP.md):** Future development plans and task tracking.
* **[models/moss/guidelines.md](models/moss/guidelines.md):** Plant care reference data for MOSS context injection.
* **[models/moss/overview.md](models/moss/overview.md):** System architecture overview for MOSS context injection.
* **[models/moss/system_prompt.md](models/moss/system_prompt.md):** MOSS AI personality and behavior rules.

---

## Directory Structure
* **`aerosense/`** — Primary Python Package
  * **`core/`** — System Logic Package
    * `__init__.py` — Package initializer
    * `controller.py` — Central control orchestrator
    * `logger.py` — CSV telemetry writer
    * `scheduler.py` — Automation cycle manager
  * **`hardware/`** — Device Drivers Package
    * `__init__.py` — Package initializer
    * `arduino.py` — Serial communication driver
    * `camera.py` — Camera hardware driver
  * **`interface/`** — User Interface Package
    * `__init__.py` — Package initializer
    * `cli.py` — Command line interface
    * `web.py` — Flask web server
  * **`ml/`** — Machine Learning Package
    * `__init__.py` — Package initializer
    * `agent.py` — MOSS AI agent
    * `health.py` — XGBoost health classifier
    * `vision.py` — Computer vision analyzer
  * `__init__.py` — Versioning and exports
  * `main.py` — Application entry point

* **`config/`** — Configuration Package
  * `__init__.py` — Package initializer
  * `settings.py` — Global system configuration

* **`data/`** — Runtime Data Storage
  * **`images/`** — Captured plant photos
  * **`logs/`** — Telemetry CSV Records
    * `camera_log.csv` — Image capture records
    * `env_log.csv` — Temperature and humidity
    * `health_log.csv` — Health classification results
    * `lights_log.csv` — Light activation events
    * `master_log.csv` — Combined sensor sweeps
    * `music_log.csv` — Song playback events
    * `pi_log.csv` — Raspberry Pi health
    * `pump_log.csv` — Pump activation events
    * `system_status.log` — System event log
    * `tiles_log.csv` — Image tiling records
    * `vision_log.csv` — Vision analysis results
    * `water_log.csv` — Water level readings
  * **`moss_conversations/`** — MOSS conversation history
    * `active_conversation.json` — Current active session
  * **`tiles/`** — Tiled image crops
  * **`tiled_vision/`** — Per-tile vision overlays
  * **`vision/`** — Stitched vision overlays

* **`firmware/`** — Arduino C++ Firmware
  * `actuators.h` — MOSFET actuator drivers
  * `config.h` — Pin and timing configuration
  * `firmware.ino` — Main firmware entry point
  * `music.h` — Passive buzzer music player
  * `sensors.h` — Sensor drivers and filters

* **`models/`** — Machine Learning Models
  * `health_model.pkl` — Trained XGBoost weights
  * **`moss/`** — MOSS AI Agent Files
    * `guidelines.md` — Plant care reference
    * `overview.md` — System overview reference
    * `stats.json` — MOSS usage statistics
    * `system_prompt.md` — MOSS personality prompt

* **`templates/`** — Web Interface Templates
  * `index.html` — Main web dashboard

* `.env` — API keys and environment variables
* `.gitignore` — Git ignore rules
* `CHANGELOG.md` — Version history and release notes
* `HARDWARE.md` — Wiring schematics and pinouts
* `README.md` — Project documentation
* `requirements.txt` — Python dependency manifest
* `ROADMAP.md` — Development roadmap

---

## Tech Stack

| Layer | Platform | Responsibilities |
|-------|----------|-----------------|
| **Application** | Raspberry Pi 5 — Python | Orchestration, scheduling, logging, ML inference, computer vision, web server, CLI |
| **Firmware** | Arduino Mega 2560 — C++ | Actuator control, sensor sampling, signal filtering, safety cutoffs, watchdog timers |
| **Web GUI** | HTML, CSS, JavaScript | 12-panel dashboard with real-time WebSocket updates, MJPEG streaming, MOSS chat |
| **Communication** | Serial UART — 115,200 baud | Newline-delimited commands with ACK verification, heartbeat monitoring, auto-reconnect |

### Python Dependencies

| Package | Purpose |
|---------|---------|
| `pyserial` | Serial communication with Arduino |
| `flask` | Web server framework |
| `flask-socketio` | WebSocket support for real-time GUI |
| `python-dotenv` | Environment variable management |
| `opencv-python` | Image processing and green pixel analysis |
| `requests` | HTTP requests to RoboFlow API |
| `numpy` | Numerical computing |
| `xgboost` | Plant health classification model |
| `scikit-learn` | ML utilities and label encoding |
| `ollama` | Local LLM client for MOSS AI agent |

### External Services
* **Ollama** — Local LLM server (installed separately).
* **RoboFlow API** — Cloud instance segmentation (requires API key).
* **rpicam-apps** — Raspberry Pi camera utilities (pre-installed on Pi OS).

---

## Getting Started

### Prerequisites
* Raspberry Pi 5 (16GB) running Raspberry Pi OS (Debian Trixie)
* Arduino Mega 2560
* Python 3.12.9 (exact, required for inference compatibility)
* Arduino IDE
* All hardware wired according to **[HARDWARE.md](HARDWARE.md)**

### 1. Navigate to Project Root
```bash
cd /home/aerosense/aerosense_prod
```

### 2. Flash Arduino Firmware
1. Open `firmware/firmware.ino` in the **Arduino IDE**.
2. Select **Board:** Arduino Mega 2560.
3. Select the correct **Port** (typically `/dev/ttyACM0`).
4. **Compile** and **Upload**.
5. Open Serial Monitor at **115,200 baud** and verify `SYSTEM:READY` appears.

### 3. Install Ollama and Pull Model
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the MOSS language model
ollama pull llama3.2:3b
```

### 4. Create Environment File
Create a `.env` file in the project root:
```
ROBOFLOW_API_KEY=your_roboflow_api_key_here
BIRTHDAYS=month,day,Name;month,day,Name
AEROSENSE_PORT=/dev/ttyACM0
```

| Variable | Required | Description |
|----------|----------|-------------|
| `ROBOFLOW_API_KEY` | Yes (for vision) | API key for RoboFlow instance segmentation. |
| `BIRTHDAYS` | No | Birthday entries as `month,day,name;...` for scheduler events. |
| `AEROSENSE_PORT` | No | Serial port override. Defaults to `/dev/ttyACM0`. |

### 5. Create Virtual Environment and Install Dependencies
```bash
# Create a virtual environment using Python 3.12
python3.12 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install packages
pip3 install -r requirements.txt
```

### 6. Launch the System
```bash
python3 -m aerosense.main
```

### Quick Start
If the firmware is already flashed and dependencies are already installed, combine into a single command:
```bash
cd /home/aerosense/aerosense_prod && source .venv/bin/activate && python3 -m aerosense.main
```

---

## System Usage

### Command Line Interface (CLI)

After launch, the system enters a command-line interface. Commands are **case-insensitive** and support **aliases** (e.g., `TEMP` maps to `ENVIRONMENT`, `CAM` maps to `CAMERA`) and **multi-word normalization** (e.g., `WATER PUMP` becomes `PUMP`, `GROW LIGHTS` becomes `LIGHTS`).

The table below is a brief overview of what's available. **Type `HELP` in the CLI for the complete command list with syntax and arguments.**

| Category | What You Can Do |
|----------|----------------|
| **Cycles** | Enable/disable automation cycles individually (`CYCLE PUMP ON`) or by group (`CYCLE SYSTEM ON`). |
| **Hardware** | Manually control the pump and lights with optional duration (`LIGHTS ON 60`). |
| **Settings** | Adjust light schedule hours and pump duration/interval at runtime (`SET PUMP DURATION 15`). |
| **Sensors** | Read environment, water level, Pi health, capture images, run vision analysis, or run the full plant health classifier. |
| **Audio** | Play songs, individual notes, or random selections by category. |
| **Diagnostics** | View system status, sync state with hardware, ping individual components. |
| **MOSS** | Chat with the AI assistant (`MOSS how are my plants?`), reset conversations, or view stats. |
| **System** | Open the web GUI (`GUI`), emergency stop (`STOP`), or shutdown (`EXIT`). |

### Web Interface (GUI)

Launch the web GUI by entering `GUI` in the CLI, then navigate to `http://<pi-ip>:5000` in a browser. The dashboard features 12 interactive panels:

| Panel | Description |
|-------|-------------|
| **MOSS Chat** | Conversational AI assistant with streaming responses. |
| **Camera** | Capture images and view the latest plant photo. |
| **Vision** | Run RoboFlow analysis and view color-coded disease overlays. |
| **Plant Health** | XGBoost health classification with 16 feature readouts. |
| **Live Stream** | Real-time MJPEG camera feed from the Pi. |
| **Automation Cycles** | Enable/disable individual or grouped automation cycles. |
| **Settings** | Adjust pump duration, pump interval, and light schedule hours. |
| **Manual Control** | Direct ON/OFF control for pump and lights with duration input. |
| **Sensors** | Read environment, water level, and Pi system health on demand. |
| **Audio** | Play songs by name, category, or random; stop playback. |
| **System** | Emergency stop and system exit controls. |
| **Developer Tools** | Remote terminal via WebSocket and hardware ping diagnostics. |

### REST API

The web GUI communicates with the backend through a REST API, a set of URL endpoints that the browser calls to read data or trigger actions. `GET` requests retrieve information (sensor readings, cycle states, settings) and `POST` requests send commands (toggle a cycle, start the pump, change a setting). Every button and panel on the dashboard maps to one of these endpoints under the hood. The `/api/status` endpoint is polled continuously by the GUI to keep the dashboard up to date.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main web dashboard. |
| `GET` | `/images/<filename>` | Serve captured image. |
| `GET` | `/vision/<filename>` | Serve vision analysis image. |
| `GET` | `/api/cycles` | Get all automation cycle states. |
| `POST` | `/api/toggle_cycle` | Toggle an individual cycle. |
| `POST` | `/api/toggle_group` | Toggle a cycle group (SYSTEM, HARDWARE, SENSORS). |
| `POST` | `/api/run_manual` | Manual hardware control (pump, lights). |
| `POST` | `/api/run_sensor` | Trigger sensor read or analysis pipeline. |
| `GET` | `/api/settings` | Get current system settings. |
| `POST` | `/api/settings` | Update a system setting. |
| `POST` | `/api/music` | Play, stop, or control music. |
| `POST` | `/api/ping` | Ping a hardware component. |
| `POST` | `/api/system` | System commands (STOP, EXIT). |
| `POST` | `/api/action` | Run system actions (SYNC, RESET). |
| `GET` | `/api/status` | Live system status (polling endpoint). |
| `GET` | `/api/stream` | MJPEG video stream. |
| `POST` | `/api/stream/start` | Start camera stream. |
| `POST` | `/api/stream/stop` | Stop camera stream. |
| `GET` | `/api/moss/status` | MOSS availability and statistics. |

### WebSocket Events

While the REST API works on a request/response basis (the browser asks, the server answers), WebSockets provide a persistent two-way connection. This is what powers the real-time features: the remote terminal streams output as it happens, and MOSS chat streams responses token by token instead of waiting for the full reply.

| Event | Direction | Description |
|-------|-----------|-------------|
| `connect` | Server → Client | Connection confirmation. |
| `command` | Client → Server | Execute CLI command remotely. |
| `terminal_output` | Server → Client | Real-time terminal output. |
| `moss_message` | Client → Server | Send message to MOSS. |
| `moss_token` | Server → Client | Streaming MOSS response token. |
| `moss_response` | Server → Client | Complete MOSS response. |

---

## System Architecture

### Hardware Overview

The system controls and monitors the following components. For specific models, pinouts, wiring, and power distribution, see **[HARDWARE.md](HARDWARE.md)**.

| Component | Purpose |
|-----------|---------|
| Water Pump | High-pressure aeroponic misting via MOSFET |
| Grow Lights | Full-spectrum LED lighting via MOSFET |
| Passive Buzzer | Acoustic feedback, alarms, and music playback |
| Environment Sensor | Temperature and humidity readings |
| Water Level Sensor | Ultrasonic distance measurement for water level |
| Camera Module | Plant image capture and live MJPEG streaming |

### Safety Interlocks

The system implements **layered, redundant safety mechanisms** across both processors:

* **Pump Runtime Limit:** Hard-capped at **30 seconds**. Enforced independently in both Python and C++ firmware.
* **Lights Runtime Limit:** Hard-capped at **24 hours**, enforced in both Python and firmware.
* **Dry-Run Protection:** Pump blocked if water level exceeds safety threshold (**100mm**).
* **Mid-Cycle Monitoring:** Water level re-checked every **2 seconds** during pump operation. Immediate shutoff + PANIC alarm if threshold exceeded.
* **Pi Heartbeat Watchdog:** Firmware shuts down all actuators if Pi goes silent for **60 seconds**.
* **Hardware Watchdog Timer:** **4-second** WDT resets the Arduino on firmware lockup.
* **Emergency Stop:** `STOP` command immediately halts all actuators and disables all cycles.

### Automation Scheduler

The scheduler manages six automation cycles. **All cycles initialize in a DISABLED state** on system boot for safety. The table below shows the default intervals, but these are just starting points. The light schedule hours, pump duration, and pump interval are all adjustable at runtime through the CLI (`SET` commands) or the GUI Settings panel. The idea is that as the health classifier and MOSS provide recommendations (e.g., "increase watering frequency" or "reduce light hours"), the user tunes these parameters accordingly.

| Cycle | Default Interval | Description |
|-------|-----------------|-------------|
| `lights` | 10:00–16:00 | Grow light window. Start and end hours are configurable. |
| `pump` | Every 30 min for 10s | Misting cycle. Both duration and interval are configurable. |
| `environment` | Every 30 min | Temperature and humidity logging. |
| `water_level` | Every 30 min | Water level logging. |
| `camera` | Every 30 min | Automated plant image capture. |
| `pi_health` | Every 30 min | CPU temperature, RAM, disk, and uptime logging. |

**Cycle Groups** allow batch control: `SYSTEM` (all 6), `HARDWARE` (pump + lights), `SENSORS` (environment + water level + camera + pi health).

---

## Data Systems

### Log Files

All telemetry is serialized to CSV files in `data/logs/`. Each file is auto-created with headers on first boot.

| File | Columns | Description |
|------|---------|-------------|
| `pump_log.csv` | Timestamp, Action, Duration_Sec | Pump activation events. |
| `lights_log.csv` | Timestamp, Action, Duration_Sec | Light activation events. |
| `env_log.csv` | Timestamp, Temp_F, Humidity_RH | Environment sensor readings. |
| `water_log.csv` | Timestamp, Level_mm | Water level readings. |
| `camera_log.csv` | Timestamp, Image_Paths | Captured image file records. |
| `master_log.csv` | Timestamp, Temp_F, Humidity_RH, Water_Level_mm, Image_Paths | Combined sensor sweeps. |
| `music_log.csv` | Timestamp, Song_Title | Song playback events. |
| `pi_log.csv` | Timestamp, CPU_Temp_C, RAM_Usage_Pct, Disk_Free_GB, Uptime_Hours | Raspberry Pi system health. |
| `tiles_log.csv` | Timestamp, Tile_1 ... Tile_6 | Image tiling records. |
| `vision_log.csv` | Timestamp, Source_Image, Total_Pixels, Green_Pixels, Chlorosis/Necrosis/Pest/Tip_Burn/Wilting_Pixels | Vision analysis pixel counts. |
| `health_log.csv` | Timestamp, 16 Features, Prediction, Confidence | Health classification results. |
| `system_status.log` | Freeform text | System-level event log. |

### Image Pipeline

The vision system follows a **Capture → Tile → Analyze → Overlay → Stitch** pipeline:

1. **`data/images/`** — Raw captured plant photos from the camera module.
2. **`data/tiles/`** — Each image is split into a **3x2 grid** (6 tiles) for granular analysis.
3. **`data/tiled_vision/`** — Each tile is sent through RoboFlow inference; color-coded disease overlays are drawn on each tile.
4. **`data/vision/`** — The 6 annotated tiles are stitched back into a single full-frame overlay image.

---

## Machine Learning

AeroSense employs three machine learning systems that work together as part of the **Sense → Analyze** pipeline. The architecture intentionally uses both **cloud-based** and **on-device** inference to demonstrate versatility.

### Computer Vision — RoboFlow Cloud API

The vision system uses the **RoboFlow instance segmentation API** to detect plant diseases at the pixel level.

* **Model:** `moss-4nrjw/3` (custom-trained instance segmentation)
* **Confidence Threshold:** 50%
* **Pipeline:** Capture image → split into 6 tiles → send each tile to RoboFlow → aggregate pixel counts → draw color-coded overlays → stitch tiles into full-frame result.

| Class | Overlay Color | Indicates |
|-------|---------------|-----------|
| Chlorosis | Yellow | Nutrient deficiency, pH imbalance. |
| Necrosis | Purple | Dead tissue, burn damage, infection. |
| Pest | Red | Insect damage, webbing, larvae. |
| Tip Burn | Orange | Nutrient burn, low humidity stress. |
| Wilting | Blue | Dehydration, heat stress, root rot. |

> **Note:** This is the cloud-based ML component. Requires `ROBOFLOW_API_KEY` in `.env`.

### Plant Health Classifier — XGBoost (Local)

An **XGBoost classifier** predicts overall plant health from **16 engineered features** spanning vision data, environmental telemetry, and temporal patterns. The model runs **entirely on-device** with no network dependency.

**Training:** The model is trained as a `.pkl` file on a separate PC (the Pi lacks the resources for training) and then transferred into `models/health_model.pkl` on the Pi for inference.

#### Health Classes

| Class | Indicates |
|-------|-----------|
| Healthy | Plant is in good condition, continue current schedule. |
| Underwatered | Not enough water. Increase pump frequency or duration. |
| Overwatered | Too much water. Reduce pump frequency or duration. |
| More_Light | Insufficient light exposure. Extend light schedule. |
| Less_Light | Excessive light exposure. Reduce light schedule. |
| Nutrient_Burn | Nutrient concentration too high. Flush and dilute. |
| Pathogen | Disease or infection detected. Isolate and treat. |

#### Features and Importance

Each prediction is built from 16 engineered features computed from vision analysis, sensor readings, and log history. The importance column measures how much each feature contributes to the model's predictions, with higher values having more influence on the final diagnosis.

| Rank | Feature | Description | Importance |
|------|---------|-------------|-----------|
| 1 | pest_density | Pest pixels as a ratio of green pixels | 0.1964 |
| 2 | instant_vpd | Vapor Pressure Deficit (kPa), from temp and humidity | 0.1609 |
| 3 | chlorosis_ratio | Chlorosis pixels as a ratio of green pixels | 0.1296 |
| 4 | tip_burn_ratio | Tip burn pixels as a ratio of green pixels | 0.1258 |
| 5 | light_interval | Total light hours in the past 24 hours | 0.1217 |
| 6 | vpd_shock | Current VPD minus 24-hour average | 0.0903 |
| 7 | wilting_ratio | Wilting pixels as a ratio of green pixels | 0.0761 |
| 8 | decay_ratio | Necrosis pixels as a ratio of green pixels | 0.0493 |
| 9 | water_volume | Net water consumed in the past 24 hours (mL) | 0.0343 |
| 10 | instant_temp | Current temperature (°F) | 0.0060 |
| 11 | growth_velocity | Percent change in green pixels between last two readings | 0.0038 |
| 12 | instant_humidity | Current relative humidity (%) | 0.0029 |
| 13 | temp_slope | Current temp minus previous reading | 0.0012 |
| 14 | delta_temp | Current temp minus 24-hour average | 0.0009 |
| 15 | time_of_day_x | Sine encoding of current hour | 0.0008 |
| 16 | time_of_day_y | Cosine encoding of current hour | 0.0001 |

### MOSS AI Agent — Ollama (Local)

**MOSS** is a conversational AI assistant that provides plant care recommendations based on live system data. It runs **entirely on-device** using Ollama — no cloud, no external API calls.

* **Model:** `llama3.2:3b` (3 billion parameters) via Ollama.
* **Context Window:** 2,048 tokens.
* **Architecture:** Keyword-based context injection, chosen over a tool-based architecture for faster and more reliable responses. When a user message contains keywords related to plant health, environment, water, lights, or system status (~50 keywords across 5 categories), the relevant data is gathered from CSV logs or live sensors and injected directly into the system prompt before calling the LLM in a single pass.
* **Streaming:** Responses stream token-by-token via WebSocket (GUI) or stdout (CLI).
* **Conversation Management:** Auto-trims at 3 message pairs to fit the context window. Conversations are archived after reset and auto-cleaned after 7 days.
* **Personality:** Friendly, concise, and knowledgeable — like a gardening expert friend. Proactively flags issues in sensor data but never fabricates readings.
* **Reference Files:** `models/moss/system_prompt.md`, `models/moss/overview.md`, `models/moss/guidelines.md`.

---

## Configuration Reference

Key settings from `config/settings.py` with their defaults:

| Setting | Default | Description |
|---------|---------|-------------|
| `SERIAL_PORT` | `/dev/ttyACM0` | Arduino serial port (overridable via `.env`). |
| `BAUD_RATE` | `115200` | Serial communication baud rate. |
| `PUMP_INTERVAL_MINS` | `30` | Minutes between automated pump cycles. |
| `PUMP_DURATION_SEC` | `10` | Pump on-time per cycle (seconds). |
| `PUMP_MAX_DURATION_SEC` | `30` | Pump safety cutoff (seconds). |
| `PUMP_SAFETY_THRESHOLD_MM` | `100` | Water level threshold to block pump (mm). |
| `LIGHTS_START_HOUR` | `10` | Automated light schedule start (24-hour). |
| `LIGHTS_END_HOUR` | `16` | Automated light schedule end (24-hour). |
| `LIGHTS_MAX_DURATION_SEC` | `86400` | Light safety cutoff (24 hours). |
| `SENSOR_INTERVAL_MINS` | `30` | Sensor logging interval (minutes). |
| `CAM_RESOLUTION` | `1920x1080` | Camera capture resolution (pixels). |
| `VISION_CONFIDENCE` | `0.50` | RoboFlow detection confidence threshold. |
| `MOSS_MODEL` | `llama3.2:3b` | Ollama model name for MOSS. |
| `MOSS_CONTEXT_LENGTH` | `2048` | LLM context window (tokens). |
| `MOSS_KEEP_ALIVE` | `30m` | Time to keep model loaded in RAM. |
| `MOSS_MAX_CONVERSATION_MESSAGES` | `3` | Message pairs before auto-trim. |

---

## Shutdown Procedure

* **`EXIT`** — Graceful shutdown. Saves MOSS conversation state, disables all automation cycles, turns off all actuators, closes the serial connection, plays the DENIED system sound, and terminates the process.
* **`STOP`** — Emergency halt. Immediately turns off all actuators and disables all cycles, but the system remains running for diagnostics.
* **`Ctrl+C`** — Triggers the same graceful shutdown sequence as `EXIT`.