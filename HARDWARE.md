# Hardware Configuration

The wiring, pinout, and power reference for AeroSense. Use this as the source of truth for assembly, replacement parts, and physical-layer debugging. Software architecture and CLI/API documentation lives in [README.md](README.md).

---

## System Block Diagram

```
POWER

    12V 200W PSU
    ├─► Water Pump        (12V, switched by D2 MOSFET)
    ├─► Grow Lights       (12V, switched by D3 MOSFET)
    └─► 12V→5V 25W Buck ─► Raspberry Pi 5  (USB-C)
                                   │
                                   └─USB-A─► Arduino Mega 2560 (USB-B)


DATA

    Pi 5 ─USB @ 115200 baud──────► Arduino Mega 2560
    Pi 5 ─CSI (CAM1, 22-pin)─────► IMX708 Camera

    Mega D2  ──signal────────────► Pump MOSFET
    Mega D3  ──signal────────────► Lights MOSFET
    Mega D4  ──PWM───────────────► Piezo Buzzer
    Mega D20 / D21 (I2C @ 0x44)──► Environment Sensor (SHT3x)
    Mega D18 / D19 (Serial1 @ 9600 baud)─► Ultrasonic Distance Sensor
```

---

## Bill of Materials

| Qty | Component | Part / Model | Interface |
| :---: | :--- | :--- | :--- |
| 1 | Application Controller | Raspberry Pi 5 (16GB) | — |
| 1 | Firmware Controller | Arduino Mega 2560 | USB-B ↔ Pi USB-A |
| 1 | Camera | IMX708 (Raspberry Pi Camera) | CSI (CAM1) |
| 1 | Environment Sensor | DFRobot **SEN0546** (Sensirion SHT3x) | I2C |
| 1 | Water Level Sensor | DFRobot **SEN0311** (waterproof ultrasonic) | UART |
| 2 | N-Channel MOSFET Module | DFRobot **DFR0457** | GPIO trigger |
| 1 | Piezo Buzzer | Passive piezo | PWM |
| 1 | Water Pump | 12V DC aeroponic pump | 12V load |
| 1 | Grow Lights | 12V LED grow light array | 12V load |
| 1 | Primary Power Supply | **12V 200W** DC PSU | AC mains in |
| 1 | Pi Power Rail | **12V→5V 25W** buck converter | 12V in / USB-C out |
| 1 | SD Card | ≥32GB, Class 10 | Pi SD slot |

---

## Power Distribution

A single **12V 200W** PSU is the only mains-connected supply. It feeds the high-current 12V loads (pump, lights) directly and steps down to 5V for the Pi through a dedicated buck converter.

| Component | Voltage | Source | Wiring Notes |
| :--- | :--- | :--- | :--- |
| **Water Pump** | 12V | 12V 200W PSU | Switched via DFR0457 N-Channel MOSFET (signal D2). |
| **Grow Lights** | 12V | 12V 200W PSU | Switched via DFR0457 N-Channel MOSFET (signal D3). |
| **Raspberry Pi 5** | 5V | 12V→5V 25W Buck | Buck converter input from 12V rail; output to Pi USB-C. |
| **Arduino Mega** | 5V | Pi 5 (USB) | Powered via USB-B from Pi USB-A. No separate supply. |
| **Sensors / Buzzer** | 5V | Arduino Mega 5V pin | Drawn from the Mega's onboard 5V regulator. |

> **Note:** The Pi is *not* powered by the official 27W Raspberry Pi PSU. Mains power enters the system through the 12V 200W PSU only.

---

## Controller: Raspberry Pi 5 (16GB)

The Pi acts as the central brain, handling telemetry, scheduling, computer vision, and the web GUI.

* **OS:** Raspberry Pi OS (Debian Trixie).
* **Camera:** IMX708 connected via CSI-to-HDMI adapter on **CAM1** (22-pin connector).
* **Arduino link:** USB-A (Pi) → USB-B (Mega).
    * **Interface:** UART over USB.
    * **Port:** `/dev/ttyACM0` (override with `AEROSENSE_PORT` env var).
    * **Baud Rate:** 115200.
    * **Timeout:** 2 seconds.
* **Storage:** SD Card.
* **Code:** [aerosense/hardware/arduino.py](aerosense/hardware/arduino.py), [aerosense/hardware/camera.py](aerosense/hardware/camera.py), [config/settings.py](config/settings.py).

---

## Controller: Arduino Mega 2560

The Arduino handles all low-level actuation, real-time sensor sampling, and safety cutoffs.

### Pinout Summary

**Actuators**
| Device | Signal Pin | Type | Logic |
| :--- | :--- | :--- | :--- |
| **Water Pump** | `D2` | Digital Out | HIGH = ON |
| **Grow Lights** | `D3` | Digital Out | HIGH = ON |
| **Buzzer** | `D4` | Digital PWM | Passive Piezo |

**Sensors**
| Device | Protocol | Pins | Driver |
| :--- | :--- | :--- | :--- |
| **Environment Sensor** | I2C | `SDA (20)`, `SCL (21)` | `Wire.h` (Address `0x44`) |
| **Water Level Sensor** | UART | `TX1 (18)`, `RX1 (19)` | `Serial1` @ 9600 baud |

### Reserved & Free Pins

* **In use:** D0/D1 (Serial0 — reserved for USB-Serial to the Pi), D2, D3, D4, D18, D19, D20, D21, plus A5 (read floating for `randomSeed` entropy — *do not* connect anything to A5).
* **Free for expansion:** all other digital pins (D5–D17, D22–D53), and analog pins A0–A4, A6–A15.

### Code Cross-Reference

* [firmware/config.h](firmware/config.h) — pin assignments, I2C address, baud rates, timing, safety limits.
* [firmware/actuators.h](firmware/actuators.h) — pump and lights drivers, hard-cap enforcement.
* [firmware/sensors.h](firmware/sensors.h) — env (SHT3x) and ultrasonic (UART) drivers, filtering, validation.
* [firmware/firmware.ino](firmware/firmware.ino) — boot sequence, command parser, watchdog.

---

## Component Wiring Detail

#### **Water Pump (DFR0457 MOSFET)**
* **Power (High Side):**
   * `VIN`  → PSU 12V
   * `GND`  → Pump & PSU GND
   * `VOUT` → Pump 12V
* **Signal (Low Side):**
   * `Red`   → 5V
   * `Black` → GND
   * `Green` → **Pin 2**

#### **Grow Lights (DFR0457 MOSFET)**
* **Power (High Side):**
   * `VIN`  → PSU 12V
   * `GND`  → Lights & PSU GND
   * `VOUT` → Lights 12V
* **Signal (Low Side):**
   * `Red`   → 5V
   * `Black` → GND
   * `Green` → **Pin 3**

> The pump and lights MOSFETs are wired identically except for the green signal wire (D2 vs D3).

#### **Buzzer**
* **Signal:**
   * `Left`   → **Pin 4**
   * `Middle` → (N/A)
   * `Right`  → GND

#### **Environment Sensor (SEN0546 — Sensirion SHT3x)**
* **Power:**
   * `Red`   → 5V
   * `Black` → GND
* **Signal:**
   * `Yellow` → **Pin 20 (SDA)**
   * `Green`  → **Pin 21 (SCL)**
* **Protocol:** I2C @ address `0x44`. Command `0x2400` (high-repeatability), 15ms settle, 6-byte response: `[Temp MSB, Temp LSB, CRC, Hum MSB, Hum LSB, CRC]`. CRC-8 polynomial `0x31`, init `0xFF` (per Sensirion datasheet).
* **Filter:** 5-sample median, 1s poll. Marked stale after 10s without a fresh sample.
* **Valid range:** −20 °F to 150 °F, 0–100 % RH. Out-of-range or CRC-failed samples are dropped silently.

#### **Water Level Sensor (SEN0311 — Ultrasonic)**
* **Power:**
   * `Red`   → 5V
   * `Black` → GND
* **Signal:**
   * `Blue`  → **Pin 18 (TX1)**
   * `Green` → **Pin 19 (RX1)**
* **Protocol:** UART on `Serial1` @ 9600 baud. 4-byte frame: `[0xFF, Distance MSB, Distance LSB, Checksum]`. Checksum = `(0xFF + MSB + LSB) & 0xFF`. Distance returned in millimeters.
* **Filter:** 15-sample trimmed mean (drops 3 highest + 3 lowest), 100ms poll. Marked stale after 5s.
* **Valid range:** 20–4500 mm. Out-of-range or checksum-failed samples are dropped silently.
* **Reservoir reference:** an empty reservoir reads ≈150–180 mm. The pump is blocked when the level reads above the **100 mm** safety threshold (configured in [config/settings.py](config/settings.py)).

---

## Boot Verification & Troubleshooting

### First-Boot Verification

After flashing the firmware:

1. Open the Arduino IDE Serial Monitor at **115200 baud**.
2. Confirm `SYSTEM:READY` is printed within ~1 s of reset.
3. Send `PING` — expect `PONG`.
4. Send `READ_TEMP` — expect `DATA_TEMP:<°F>,<%RH>` (may take a few seconds while the median buffer fills).
5. Send `READ_DISTANCE` — expect `DATA_DISTANCE:<mm>`.
6. Send `PUMP ON 1000` — expect `ACK:PUMP_ON,1000`, followed by `ALERT:TIMER_COMPLETE` after 1 second.

### Common Issues

| Symptom | Likely Cause | Fix |
| :--- | :--- | :--- |
| `/dev/ttyACM0` not present on Pi | USB cable not enumerating, or Mega enumerated as a different port | Re-seat USB-B cable; if the Mega appears as `/dev/ttyACM1`, set `AEROSENSE_PORT` in `.env`. |
| `READ_TEMP` returns nothing | Env sensor stale (>10 s without valid data) | Verify Yellow→D20 (SDA), Green→D21 (SCL), and 5V/GND on the sensor; address must be `0x44`. |
| `READ_DISTANCE` returns nothing | Distance sensor stale (>5 s) | Verify Blue→D18 (TX1), Green→D19 (RX1), and 5V/GND; ensure no other library is using `Serial1`. |
| Pump refuses to start | Water level reads above the 100 mm safety threshold (reservoir empty) | Refill reservoir; verify the ultrasonic is mounted at the top of the tank, pointing down. |
| MOSFET load not switching | Signal-side miswired | On each DFR0457: Red→5V, Black→GND, Green→signal pin (Pump=D2, Lights=D3). |
| Arduino resets every ~4 s | Firmware lockup → 4-second hardware watchdog firing | Check serial output for the last line before reset; verify power stability and that no blocking calls were added. |
| Pump and lights both shut off unexpectedly | Pi heartbeat watchdog (60 s without command) | Confirm the Pi-side process is running; firmware emits `ALERT:PI_TIMEOUT` when this fires. |
