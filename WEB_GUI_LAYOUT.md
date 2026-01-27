# AeroSense Web GUI - Visual Layout

```
┌─────────────────────────────────────────────────────────────────┐
│                     AEROSENSE v3.8.4                            │
│         System Online • Garden Control • Last Update: now        │
└─────────────────────────────────────────────────────────────────┘

┌─ 📷 LIVE CAMERA FEED ───────────────────────────────────────────┐
│                                                                   │
│  [Image Display Area]                                            │
│  📸 Captured: 23s ago                                            │
│                                                                   │
│  [📸 CAPTURE PHOTO]  [🎥 LIVE CAMERA]                           │
└───────────────────────────────────────────────────────────────────┘

┌─ ⚙️ AUTOMATION CYCLES ──────────────────────────────────────────┐
│  Group Controls:                                                  │
│  [SYSTEM]  [HARDWARE]  [SENSORS]                                │
│                                                                   │
│  Individual Cycles:                                              │
│  [PUMP]    [LIGHTS]   [ENVIRONMENT]  [WATER LEVEL]             │
│  [CAMERA]  [PI HEALTH]                                          │
└───────────────────────────────────────────────────────────────────┘

┌─ 🎮 MANUAL HARDWARE CONTROL ───────────────────────────────────┐
│                                                                   │
│  💡 LIGHTS Control                                               │
│  [✓ ON]  [Duration]  [✗ OFF]                                   │
│                                                                   │
│  💧 PUMP Control                                                 │
│  [✓ ON]  [Duration]  [✗ OFF]                                   │
│                                                                   │
│  [🔍 RUN FULL SENSOR SWEEP]                                    │
│                                                                   │
│  Environment Readings:                                           │
│  [🌡️ ENVIRONMENT]  [92.5°F] [65%]      (23s ago)              │
│                                                                   │
│  Water Level:                                                    │
│  [💧 WATER LEVEL]  [128 mm]            (4m ago)                │
│                                                                   │
│  Pi Health:                                                      │
│  [🖥️ PI HEALTH]                                                 │
│  CPU: 42°C  RAM: 38%  DISK: 15.2GB  UPTIME: 72h               │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ 🎵 AUDIO CONTROL ─────────────────────────────────────────────┐
│  [⏹️ STOP]  [▶️ RANDOM]                                          │
│                                                                   │
│  Available Tracks:                                               │
│  [DAISY]  [MV1]  [ULTRON]  [FNAF]  [MORNING]  [SLEEP]          │
│  [CURIOSITY]  [TARS]  [PANIC]  [WARNING]  [TEST]  [etc...]     │
└───────────────────────────────────────────────────────────────────┘

┌─ 🔧 DIAGNOSTICS & STATUS ──────────────────────────────────────┐
│  Quick Ping Groups:                                              │
│  [SYSTEM]  [HARDWARE]  [SENSORS]                                │
│                                                                   │
│  Component Health:                                               │
│  ┌─────────┬─────────┬─────────┬─────────────┐                 │
│  │ SYSTEM  │  PUMP   │ LIGHTS  │ ENVIRONMENT │                 │
│  │ ✓ OK    │ ✓ OK    │ ✓ OK    │ ✓ OK        │                 │
│  └─────────┴─────────┴─────────┴─────────────┘                 │
│  ┌─────────────┬──────────┬────────┬─────────┐                 │
│  │ WATER LEVEL │ CAMERA   │ BUZZER │         │                 │
│  │ ✓ OK        │ ✓ OK     │ ✓ OK   │         │                 │
│  └─────────────┴──────────┴────────┴─────────┘                 │
│                                                                   │
│  [🔄 SYNC STATE]  [🔧 RESET]                                   │
└───────────────────────────────────────────────────────────────────┘

┌─ ⚡ SYSTEM CONTROL ────────────────────────────────────────────┐
│  ⚠️ Warning: Emergency Stop will halt all operations!           │
│                                                                   │
│  [🛑 EMERGENCY STOP]      [🚪 EXIT SYSTEM]                     │
└───────────────────────────────────────────────────────────────────┘

AeroSense Garden Controller | Built with 💚 for Plant Automation
```

---

## Component Breakdown

### Header Section
- System status indicator (green dot = online)
- Version display
- Quick status info
- Auto-update timestamp

### Camera Section
- Large image display area
- Timestamp of capture
- Capture photo button (5sec wait)
- Live camera stream option

### Automation Cycles
- Group toggles for quick control
- Individual cycle switches (visual feedback: green=on, gray=off)
- Color-coded status

### Manual Control
- Lights: ON/OFF with optional duration
- Pump: ON/OFF with optional duration
- Full sensor sweep option
- Individual sensor triggers:
  - Environment (temp + humidity)
  - Water level (mm reading)
  - Pi health (4 metrics)

### Audio Control
- Stop button (red)
- Random play (green)
- Song selection grid (all available tracks)

### Diagnostics
- 3 quick ping buttons (system groups)
- 7 individual component health cards
- Each shows status and last update time
- Sync and reset operations

### System Control
- Emergency Stop (red, requires confirmation)
- Exit System (gray, requires confirmation)

---

## Color-Coded Status

| Color | Meaning | Used For |
|-------|---------|----------|
| 🟦 Cyan | Active/Primary | Accent color, buttons, online status |
| 🟩 Green | Success/Running | Toggle-on state, ON buttons, healthy |
| 🟥 Red | Stop/Danger | OFF buttons, emergency stop |
| 🟨 Yellow | Important | Full sensor sweep |
| ⬜ Gray | Inactive/Secondary | Toggle-off state, group buttons |

---

## Responsive Breakpoints

```
Desktop (1400px width):
├── 4-column grids
├── Side-by-side layouts
└── Full feature set

Tablet (768px width):
├── 2-column grids
├── Stacked layouts
└── Touch-friendly buttons

Mobile (< 768px):
├── Single column
├── Full-width buttons
├── Stacked sections
└── Swipe-friendly
```

---

## Browser Compatibility

| Browser | Status | Notes |
|---------|--------|-------|
| Chrome | ✅ Full | Optimal experience |
| Firefox | ✅ Full | Full support |
| Safari | ✅ Full | iOS friendly |
| Edge | ✅ Full | Chromium-based |
| Mobile | ✅ Full | Responsive design |

---

## Features Covered

✅ Camera Management  
✅ Automation Control  
✅ Hardware Actuation  
✅ Sensor Reading  
✅ Audio Control  
✅ Diagnostics  
✅ System Control  
✅ Real-time Updates  
✅ Error Handling  
✅ Mobile Responsive  
✅ Professional UI  
✅ Keyboard Shortcuts  

**All files associated with JCT now have GUI coverage! 🎉**
