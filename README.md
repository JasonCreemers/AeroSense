# AeroSense Garden Controller
**Version: v3.0.0** | **Release: 2026-01-10**

AeroSense is an advanced aeroponic gardening controller. It utilizes a **Raspberry Pi 4B** for high-level system control, data logging, and computer vision, while an **Arduino Mega 2560** handles low-level actuation and real-time sensor monitoring.

---

## To Do List
### Immediate Tasks
* Make README.md more professional
* Maybe add ROADMAP.md
* Spongebob sad song


### Upcoming Tasks
* System Changes
   * Clean up serial communication and variables
      * MAYBE: rewrite firmware.ino to use C-style character arrays char[] and strtak
* Sensor Changes
   * Better filtering on sensors
   * More Pi commands
   * Add High/Medium/Low water level check
* Actuation Changes
   * More safety features
* Music Changes
   * Maybe an octave shifter?
   * Akron fight song/alma mater
   * Make random code on the python side, and divide songs into happy, sad, etc.


### Long Term Tasks
* System Changes
   * Make a local HTML GUI
   * Make a web-based HTML GUI
* MOSS Changes
   * Make a computer vision AI model
   * Make a YOLO AI model
      * Allow it to play music

---

## Changelog
* **v3.0.0** | 2026-01-10
   * Integrated final code with physical system.
* **v2.2.2** | 2026-01-09
   * Modified birthday code.
   * Added many more audio cues for errors/positive alerts.
* **v2.2.1** | 2026-01-07
   * Fixed ghost threads bottleneck for real in `cotroller.py`.
* **v2.2.0** | 2026-01-07
   * Added timestamping when getting latest data to prevent stale data in `arduino.py`.
   * Fixed ghost threads bottleneck in `controller.py`
* **v2.1.2** | 2026-01-07
   * Fixed `Reset` command and added manual override to status.
* **v2.1.1** | 2026-01-07
   * Added a new `Reset` command.
   * Cleaned up many print statements.
   * Changed morning tune to only occur at 8AM instead of whenever cycle is enabled.
   * General code cleanup and optimization.
* **v2.1.0** | 2026-01-07
   * Incorporated GitHub.
   * Fixed issue with camera lights not working outside active window.
   * Cleaned up code in `main.py`.
   * Fixed synoynm checking for cycle command.
* **v2.0.1** | 2026-01-06
   * Added new commands synonynms.
   * Cleaned up versioning and release variables.
   * Added light logs when turned on for camera.
   * Added result prints to `RUN SENSORS`.
   * Added lots of new songs, as well as morning and evening music synced with the lights.
   * Modified `MUSIC PLAY NOTE [NOTE] [SEC]` command.
   * Modified controller so it can recognize pump is turned off after 30s and not freak out.
* **v2.0.0** | 2026-01-04
   * Complete revamp of entire system architecture.
* **v1.7.0** | 2025-12-30
* **v1.6.0** | 2025-12-30
* **v1.5.0** | 2025-12-30
* **v1.4.0** | 2025-12-30
* **v1.3.0** | 2025-12-28
* **v1.2.0** | 2025-12-28
* **v1.1.0** | 2025-12-19
* **v1.0.0** | 2025-12-05

---

## Directory Structure
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
  * `__init__.py`: Package initialization and versioning.
  * `main.py`: AeroSense application entry point.

* **`config/`**
  * `__init__.py`
  * `settings.py`: System configuration and global variables - Python.

* **`data/`** - Data Package
  * **`images/`** - Image Storage
  * **`logs/`** - Telemetry Records
     * `camera_log.csv`
     * `environment_log.csv`
     * `lights_log.csv`
     * `music_log.csv`
     * `pi_log.csv`
     * `pump_log.csv`
     * `system_status.log`
     * `water_log.csv`

* **`firmware/`** - Microcontroller Unit (MCU) Package
  * `actuators.h`: Control logic for actuator MOSFETs.
  * `config.h`: System configuration and global variables - Arduino.
  * `firmware.ino`: Main Arduino firmware entry point.
  * `music.h`: Passive buzzer music player.
  * `sensors.h`: Sensor drivers and processors.

* `.gitignore`: Ignore sensitive and irrelevant files.
* `README.md`: System documentation, hardware setup, and usage.
* `requirements.txt`: Python dependency manifest.

---

## Arduino Hardware Configuration
### **Arduino Mega 2560**

### **Water Pump (DFR0457 MOSFET)**
* **Power:** 
   * VIN | PSU 12V
   * GND | Pump & PSU GND
   * VOUT | Pump 12V
* **Signal:**
   * Red | 5V
   * Black | GND
   * Green | Pin 2

### **Grow Lights (DFR0457 MOSFET)**
* **Power:**
   * VIN | PSU 12V
   * GND | Lights & PSU GND
   * VOUT | Lights 12V
* **Signal:**
   * Red | 5V
   * Black | GND
   * Green | Pin 3

### **Environment Sensor (SEN0546 Temperature/Humidity)**
* **Interface:** 
   * I2C
* **Power:**
   * Red | 5V
   * Black | GND
* **Signal:**
   * Yellow | Pin 20 (SDA)
   * Green | Pin 21 (SCL)

### **Water Level Sensor (SEN0311 Ultrasonic)**
* **Interface:** 
   * Serial
* **Power:**
   * Red | 5V
   * Black | GND
* **Signal:**
   * Blue | Pin 18 (TX1)
   * Green | Pin 19 (RX1)

### **Audio (Passive Buzzer)**
* **Signal:**
   * Left | Pin 4
   * Middle (N/A)
   * Right | GND

---

## Raspberry Pi Hardware Configuration
### **Raspberry Pi 4B**

### Power
* **Connection:**
   * 5V | USB-C

### Controller (Arduino Mega 2560)
* **Interface:** 
   * UART over USB (Serial-to-TTL)
* **Connection:**
   * USB-A (Pi) | USB-B (Mega)
* **Port:**
   * /dev/ttyACM0
* **Protocol:**
   * 115200 Baud

### Camera (IMX708)
* **Interface:**
   * MIPI CSI (Camera Serial Interface)
* **Connection:**
   * CSI (Camera) | HDMI | CSI (Pi)

---

## Getting Started
 
### 1. Firmware Initialization
1. Ensure all hardware is correctly wired according to the pinout above.
2. Compile and upload `firmware/aerosense_mega.ino` to the Arduino Mega.

### 2. Software Installation
Install the required Python dependencies:
```bash
pip3 install -r requirements.txt
```

### 3. Launching the System
Navigate to the project root and execute the main module.
```bash
# Navigate to project root
cd ~/AeroSense/AeroSense

# Launch main module
python3 -m aerosense.main
```

---

## How to Use

### System Operation
After launching the main module, the user enters a command line interface (CLI). This interface serves as the central control plane, displaying real-time system status and accepting operator commands to control system parameters.

To view a list of all system commands available, the user may enter the `HELP` command.

### Control Modes
The controller supports two different operational modes:
1. **Manual Activation:** Immediate control over individual hardware components.
1. **Automated Scheduling:** Enabling of "Cycles" to allow the internal scheduler to manage hardware components.
>**Operational Note:** To ensure hardware safety, all automation cycles initialize in a **DISABLED** state upon system launch.

### System Capabilities
The controller manages an array of integrated hardware subsystems, including:
* **Acutation:**
   * Water Pump
   * Grow Lights
* **Telemetry:**
   * Environmental Sensing (Temperature/Humidity)
   * Water Level Sensing (Ultrasonic)
* **Imaging:**
   * Camera Module
* **Feedback:**
   * Acoustic Alerts (Passive Buzzer)

### Data Persistence
All system events are serialized and stored within the local `data/` directory.
* **Telemetry and Actuation:** Sensor data and state changes are appended to CSV logs in `data/logs/`.
* **Imaging:** Captured images are saved to `data/images/`.

### Safety Interlocks
The system architecture includes critical fail-safes to prevent hardware damage. This includes logic such as water level verification before pump operation.

### Shutdown Procedure
To terminate the session, the user must issue the `EXIT` command. This triggers a shutdown sequence that disables all active cycles and secures hardware connections before terminating the process.