# 🎮 AeroSense Web GUI - Quick Reference Card

## 🚀 Getting Started

```bash
cd /home/jason/jct
python main.py
```

**Access:** http://localhost:5000

---

## 📍 Navigation Map

```
HEADER
├── System Status (✓ Online)
├── Version Info
└── Last Update Timestamp

📷 LIVE FEED
├── Camera Image Display
├── Capture Photo Button
└── Live Camera Stream

⚙️ AUTOMATION
├── Group Controls (System/Hardware/Sensors)
└── Individual Cycle Toggles

🎮 MANUAL CONTROL
├── 💡 Lights (On/Off/Duration)
├── 💧 Pump (On/Off/Duration)
└── 🔍 Sensors
    ├── Environment (Temp/Humidity)
    ├── Water Level (mm)
    └── Pi Health (CPU/RAM/Disk/Uptime)

🎵 AUDIO
├── Stop Button
├── Random Play
└── Track Selection Grid

🔧 DIAGNOSTICS
├── Quick Ping (System/Hardware/Sensors)
├── Component Health (7 cards)
├── Sync State
└── Reset

⚡ SYSTEM
├── Emergency Stop
└── Exit System

FOOTER
└── Copyright/Attribution
```

---

## 🎯 Common Tasks

### 📸 Capture Photo
1. Click **"📸 CAPTURE PHOTO"**
2. Wait ~5 seconds
3. Photo appears at top

### 💡 Turn on Lights
1. Enter duration (seconds)
2. Click **"✓ ON"**
3. Duration timer starts

### 🌡️ Check Environment
1. Click **"🌡️ ENVIRONMENT"**
2. View temp + humidity instantly
3. Shows last update time

### 🔊 Play Music
1. Choose track from grid
2. Click button
3. Music plays immediately

### 🛑 Emergency Stop
1. Scroll to **"⚡ SYSTEM"**
2. Click **"🛑 EMERGENCY STOP"**
3. Confirm prompt
4. All operations halt

---

## 🎨 Button Legend

| Button | Color | Purpose |
|--------|-------|---------|
| CAPTURE PHOTO | 🔵 Blue | Take photo |
| ON | 🟢 Green | Start operation |
| OFF | 🔴 Red | Stop operation |
| ENVIRONMENT | ⬜ Gray | Check sensor |
| EMERGENCY STOP | 🔴 Red | Halt all |
| SYNC STATE | 🔵 Blue | Resync system |
| GROUP TOGGLES | ⬜ Gray | Control groups |
| TRACK BUTTONS | ⬜ Gray | Play audio |

---

## 📊 Status Indicators

| Status | Meaning |
|--------|---------|
| 🟩 Toggle On | Cycle is active |
| ⬜ Toggle Off | Cycle is inactive |
| 🟩 ✓ OK | Component healthy |
| 🔴 Error | Component issue |
| ✨ Online | System ready |

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Alt + R | Refresh page |
| Alt + S | Quick stop (expandable) |

---

## 🔌 Controlled Components

```
HARDWARE
├── Pump (Water delivery)
├── Lights (Grow lights)
├── Buzzer (Audio alerts)
└── Camera (Photo/video)

SENSORS
├── Temperature sensor
├── Humidity sensor
├── Water level sensor
└── Pi system monitor

SOFTWARE
├── Scheduler (Automation)
├── Controller (Logic)
└── Logger (Data tracking)
```

---

## 📱 Device Compatibility

| Device | Status | Notes |
|--------|--------|-------|
| Desktop | ✅ Full | Best experience |
| Laptop | ✅ Full | Full support |
| Tablet | ✅ Full | Touch-friendly |
| Phone | ✅ Full | Responsive |

---

## 🔍 Troubleshooting Quick Tips

| Problem | Solution |
|---------|----------|
| Page won't load | Check Arduino is connected |
| Buttons not responding | Click "🔄 SYNC STATE" |
| Photo won't upload | Check /data/images/ permissions |
| Web server won't start | Verify port 5000 is free |
| Styling looks broken | Refresh (Ctrl+Shift+Delete) |
| Commands fail | Check system logs |

---

## 📈 Real-Time Data Fields

```
Temperature:   92.5°F              (Last update: 23s ago)
Humidity:      65%                 (Last update: 23s ago)
Water Level:   128 mm              (Last update: 4m ago)

Pi Health:
├── CPU Temp:  42°C
├── RAM Usage: 38%
├── Disk Free: 15.2GB
└── Uptime:    72 hours
```

---

## 🎛️ Control Groups

### SYSTEM (All Components)
Toggles: Lights + Pump + Environment + Water + Camera + Pi Health

### HARDWARE (Physical Actuators)
Toggles: Lights + Pump

### SENSORS (Data Collection)
Toggles: Environment + Water Level + Camera + Pi Health

---

## 🎵 Available Audio Tracks

**Happy:** DAISY, MV1  
**Angry:** ULTRON, FNAF  
**Other:** MORNING, SLEEP, CURIOSITY, TARS  
**System:** PANIC, WARNING, TEST, GRANTED, DENIED  

---

## ✅ Safety Features

- ✅ Confirmation required for Emergency Stop
- ✅ Confirmation required for Exit System
- ✅ Duration limits on pump/lights
- ✅ Error alerts for failed operations
- ✅ Real-time status monitoring
- ✅ Component health checks

---

## 🔧 Configuration Reference

Located in: `aerosense/config/settings.py`

```python
SERIAL_PORT         /dev/ttyACM0
BAUD_RATE          115200
PUMP_INTERVAL_MINS 30
PUMP_DURATION_SEC  10
LIGHTS_START_HOUR  10
LIGHTS_END_HOUR    16
SENSOR_INTERVAL    30 mins
```

---

## 📊 Data Cache Display

The dashboard shows cached data from the Controller:
- Latest photo timestamp
- All sensor readings
- Component ping statuses
- System health metrics

Cache updates on each action via API.

---

## 🌐 Access Methods

```bash
# Local network
http://192.168.1.100:5000

# If on Raspberry Pi directly
http://localhost:5000

# Through SSH tunnel
ssh -L 5000:localhost:5000 user@pi_ip
http://localhost:5000
```

---

## 🎓 Learning Resources

1. **Feature Guide** → Read: `WEB_GUI_GUIDE.md`
2. **Layout Details** → Read: `WEB_GUI_LAYOUT.md`
3. **Full Summary** → Read: `WEB_GUI_SUMMARY.md`
4. **API Endpoints** → Check: `aerosense/interface/web.py`

---

## 🚨 Emergency Procedures

**If system becomes unresponsive:**
1. Click **"🛑 EMERGENCY STOP"** and confirm
2. Wait 3 seconds
3. System halts all operations

**To fully exit:**
1. Click **"🚪 EXIT SYSTEM"** and confirm
2. Web server stops
3. CLI terminates
4. System offline

---

## 📝 Tips & Tricks

- 💡 **Set duration to 0** for infinite run (until manual OFF)
- 🎵 **Click RANDOM** multiple times to queue tracks
- 🔄 **Use SYNC STATE** after any manual Arduino changes
- 📸 **Check CAMERA ping** if photos aren't saving
- 🌡️ **Full SENSOR SWEEP** runs all sensors at once
- ⏰ **Cycles run automatically** when enabled

---

## 🔐 Data Safety

- ✅ All data stored locally in `/data/`
- ✅ Logs stored in `/data/logs/`
- ✅ Photos stored in `/data/images/`
- ✅ No cloud upload by default
- ✅ Manual backups: Copy `/data/` folder

---

## 🎉 You're All Set!

Your AeroSense garden is now controllable via web interface! 🌱

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Support:** Check documentation guides  

🌱 **Happy Gardening!** 🌱
