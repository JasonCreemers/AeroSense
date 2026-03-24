# AeroSense Garden Controller
**Version: v4.3.3** | **Release: 2026-03-24**

**AeroSense** is a high-performance, hybrid automation system designed for aeroponic gardening. It utilizes a **Raspberry Pi 4B** for high-level system control, data logging, and computer vision, while an **Arduino Mega 2560** handles low-level actuation and real-time sensor monitoring.

---

## Documentation
* **[CHANGELOG.md](CHANGELOG.md):** Version history and release notes.
* **[HARDWARE.md](HARDWARE.md):** Wiring schematics, pinouts, and power distribution.
* **[README.md](README.md):** Project overview, installation instructions, and operational manual.
* **[ROADMAP.md](ROADMAP.md):** Future development plans and task tracking.

---
## Directory Structure
* **`.venv/`** - Virtual Environment Configuration

* **`aerosense/`** - Primary Python Package
  * **`core/`** - System Logic Package
     * `__init__.py`
     * `controller.py`: Central controls logic and state management.
     * `logger.py`: Central system logger.
     * `scheduler.py`: Automated system scheduler.
  * **`hardware/`** - Device Drivers Package
     * `__init__.py`
     * `arduino.py`: Serial communication driver.
     * `camera.py`: Camera hardware driver.
  * **`interface/`** - User Interface Package
     * `__init__.py`
     * `cli.py`: Command line interface processor.
     * `web.py`: Flask web server for the graphical user interface.
  * **`ml/`** - Machine Learning Package
     * `__init__.py`
     * `health.py`: XGBoost plant health classifier.
     * `vision.py`: Computer vision analyzer.
  * `__init__.py`: Package initialization and versioning.
  * `main.py`: AeroSense application entry point.

* **`models/`** - Machine Learning Models
  * `health_model.pkl`: Trained XGBoost model weights.

* **`config/`**
  * `__init__.py`
  * `settings.py`: System configuration and global variables - Python.

* **`data/`** - Data Package
  * **`images/`** - Image Storage
  * **`logs/`** - Telemetry Records
     * `camera_log.csv`
     * `environment_log.csv`
     * `health_log.csv`
     * `lights_log.csv`
     * `music_log.csv`
     * `pi_log.csv`
     * `pump_log.csv`
     * `system_status.log`
     * `tiles_log.csv`
     * `vision_log.csv`
     * `water_log.csv`
  * **`tiles/`** - Tiled Image Storage
  * **`vision/`** - Vision Analysis Storage

* **`firmware/`** - Microcontroller Unit (MCU) Package
  * `firmware.ino`: Main Arduino firmware entry point.
  * `actuators.h`: Control logic for actuator MOSFETs.
  * `config.h`: System configuration and global variables - Arduino.
  * `music.h`: Passive buzzer music player.
  * `sensors.h`: Sensor drivers and processors.

* **templates/** - Web Interface GUI Package
   * `index.html`: Main web dashboard template for system control.

* `.env`: Environment variables for secure API key management.
* `.gitignore`: Ignore sensitive and irrelevant files.
* `CHANGELOG.md`: Version history and release notes.
* `HARDWARE.md`: Wiring schematics, pinouts, and power distribution.
* `README.md`: Project overview, installation instructions, and operational manual.
* `requirements.txt`: Python dependency manifest.
* `ROADMAP.md`: Future development plans and task tracking.

---

## Getting Started

### 1. Navigate to Project Root
Open up a terminal session and navigate to the project root.
```bash
# Navigate to project root
cd /home/aerosense/aerosense_prod
```

### 2. Firmware Initialization
1. Ensure all hardware is correctly wired according to **[HARDWARE.md](HARDWARE.md)**.
2. Open `firmware/firmware.ino` in the Arduino IDE.
3. Compile and upload to the **Arduino Mega 2560**.

### 3. Initalize Environment
Initialize the virtual environment.
```bash
# Initialize environment
source .venv/bin/activate
```

### 4. Software Installation
Install the required Python dependencies:
```bash
# Install packages
pip3 install -r requirements.txt
```

### 5. Launching the System
Execute the main module.
```bash
# Launch main module
python3 -m aerosense.main
```

## Quick Start
**Note:** If the firmware is already initialized (Step 2) and the software is already installed (Step 4), then Steps 1, 3, and 5 can be combined into a single command.
```bash
# Navigate to project root, initialize environment, and launch main module
cd /home/aerosense/aerosense_prod && source .venv/bin/activate && python3 -m aerosense.main
```

---

## How to Use

### System Operation
After launching the main module, the user enters a **Command Line Interface (CLI)**. This interface serves as the central control plane, displaying real-time system status and accepting operator commands.

To view a list of all available commands, enter: `HELP`.

### Control Modes
The controller supports two different operational modes:
1. **Manual Activation:** Immediate control over individual hardware components via CLI.
1. **Automated Scheduling:** The internal scheduler manages "Cycles" for lights and pumps based on the time of day.
>**Operational Note:** To ensure safety, all automation cycles initialize in a **DISABLED** state upon system launch.

### System Capabilities
The AeroSense controller manages a distributed array of hardware subsystems:
* **Actuation & Control**
   * **Water Pump:** 12V High-pressure pump.
   * **Grow Lights:** 12V Full-spectrum LED array.
* **Precision Telemetry**
   * **Environmental:** Real-time Temperature & Humidity sensing.
   * **Water Level:** Contactless Ultrasonic Water Level sensing.
* **Computer Vision**
   * **Imaging:** 12MP Wide-angle Camera Module.
* **Human Interface**
   * **Feedback:** Context-aware acoustic alerts.\
   * **Control:** Command Line Interface (CLI) via Serial/SSH.

### Data Persistence
All system events are serialized and stored within the local `data/` directory.
* **Telemetry and Actuation:** Sensor data and state changes are appended to CSV logs in `data/logs/`.
* **Imaging:** Captured images are saved to `data/images/`.

### Safety Interlocks
The system architecture includes critical fail-safes to prevent hardware damage:
* **Dry Run Protection:** The firmware prevents pump operation if the ultrasonic sensor detects a low water level.
* **Runtime Limits:** Both Python and Firmware enforce maximum runtime limits on the pump to prevent flooding.

### Machine Learning
*Coming soon.*

### Shutdown Procedure
To terminate the session, the user must issue the `EXIT` command. This triggers a shutdown sequence that disables all active cycles, stops the actuators, and secures the serial connection before terminating.