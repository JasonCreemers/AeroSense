# Hardware Configuration

## Power Distribution
| Component | Voltage | Source | Wiring Notes |
| :--- | :--- | :--- | :--- |
| **Arduino Mega** | 5V | USB | Powered via USB-B from Raspberry Pi. |
| **Raspberry Pi 4B** | 5V | PSU | Powered via USB-C from buck converter. |
| **Grow Lights** | 12V | PSU | Switched via N-Channel MOSFET. |
| **Water Pump** | 12V | PSU | Switched via N-Channel MOSFET. |

---

## Controller: Raspberry Pi 4B
The Pi acts as the central brain, handling telemetry, scheduling, and computer vision.

### Peripherals
* **Camera:** IMX708 connected via CSI-to-HDMI adapter.
* **Controller:** Arduino Mega 2560 connected via USB-A (Pi) to USB-B (Mega).
    * **Interface:** UART.
    * **Port:** `/dev/ttyACM0`.
    * **Baud Rate:** 115200.
* **Storage:** SD Card.

---

## Controller: Arduino Mega 2560
The Arduino handles all low-level actuation and real-time sensor logic.

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
| **Water Level Sensor** | UART | `TX1 (18)`, `RX1 (19)` | `Serial1` |

### Component Wiring Detail

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

#### **Buzzer**
* **Signal:**
   * `Left`   → **Pin 4**
   * `Middle` → (N/A)
   * `Right`  → GND

#### **Environment Sensor (SEN0546 Temperature/Humidity)**
* **Power:**
   * `Red`   → 5V
   * `Black` → GNDy "git commit" with one argument, the name of the file
# that has the commit message.  The hook should exit with non-zero
# status after issuing an appropriate message if it wants to stop the
# commit.  The hook is allowed to edit the commit message file.
#
# To enable this hook, rename this file to "commit-msg".

# Uncomment the below to add a Signed-off-by line to the message.
# Doing this in a hook is a bad idea in general, but the prepare-commit-msg
# hook is more suited to it.
#
# SOB=$(git var GIT_AUTHOR_IDENT | sed -n 's/^\(.*>\).*$/Signed-off-by: \1/p')
# grep -qs "^$SOB" "$1" || echo "$SOB" >> "$1"

# This example catches duplicate Signed-off-by lines.
* **Signal:**
   * `Yellow` → **Pin 20 (SDA)**
   * `Green`  → **Pin 21 (SCL)**

#### **Water Level Sensor (SEN0311 Ultrasonic)**
* **Power:**
   * `Red`   → 5V
   * `Black` → GND
* **Signal:**
   * `Blue`  → **Pin 18 (TX1)**
   * `Green` → **Pin 19 (RX1)**