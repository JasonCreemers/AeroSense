# AeroSense Web GUI - Complete Guide

## Overview
A modern, responsive web interface for the AeroSense Garden Controller has been created. The GUI provides complete control and monitoring of all system components through an intuitive dashboard.

**Access:** `http://localhost:5000`

---

## Features

### 1. 📷 **Live Camera Feed**
- Display latest captured photo from camera
- **CAPTURE PHOTO** - Take a burst of photos using the camera module
- **LIVE CAMERA** - Stream live HDMI camera feed

### 2. ⚙️ **Automation Cycles**
- **Group Controls** - Toggle entire subsystems (SYSTEM, HARDWARE, SENSORS)
- **Individual Cycles** - Fine-grained control over each automation cycle:
  - Pump scheduling
  - Lights scheduling
  - Environment monitoring
  - Water level detection
  - Camera automation
  - Pi health checks

### 3. 🎮 **Manual Hardware Control**
- **💡 LIGHTS Control** - Turn on/off with optional duration
- **💧 PUMP Control** - Turn on/off with optional duration
- **🔍 Sensor Suite**:
  - **ENVIRONMENT** - Read temperature & humidity
  - **WATER LEVEL** - Check reservoir status
  - **PI HEALTH** - Monitor CPU, RAM, Disk, Uptime

### 4. 🎵 **Audio Control**
- **STOP** - Stop currently playing audio
- **RANDOM** - Play random track from library
- **Track Selection** - All available songs displayed:
  - Happy: DAISY, MV1
  - Angry: ULTRON, FNAF
  - Other: MORNING, SLEEP, CURIOSITY, TARS
  - System: PANIC, WARNING, TEST, GRANTED, DENIED

### 5. 🔧 **Diagnostics & Status**
- **Component Health** - Check status of all connected components:
  - SYSTEM
  - PUMP
  - LIGHTS
  - ENVIRONMENT
  - WATER SENSOR
  - CAMERA
  - BUZZER
- **Quick Ping Groups** - Test entire subsystem groups
- **SYNC STATE** - Synchronize system state with hardware
- **RESET** - Reset all overrides

### 6. ⚡ **System Control**
- **🛑 EMERGENCY STOP** - Halt all operations immediately (with confirmation)
- **🚪 EXIT SYSTEM** - Gracefully shut down the system (with confirmation)

---

## Technical Architecture

### Backend (Python)
**File:** `aerosense/interface/web.py`

The WebServer class provides:
- Flask-based HTTP API on port 5000
- 11+ API endpoints for complete system control
- Thread-safe communication with Controller and Scheduler
- Background daemon thread operation
- Real-time data cache display

**Key Endpoints:**
```
POST /api/toggle_cycle          - Toggle individual cycles
POST /api/toggle_group          - Toggle cycle groups
POST /api/run_manual            - Control lights/pump
POST /api/run_sensor            - Trigger sensor readings
POST /api/music                 - Control audio playback
POST /api/ping                  - Check component health
POST /api/action                - SYNC/RESET operations
POST /api/system                - STOP/EXIT commands
GET  /                          - Main dashboard
GET  /images/<filename>         - Serve captured images
```

### Frontend (HTML/CSS/JavaScript)
**File:** `templates/index.html`

Modern responsive design featuring:
- **Monospace terminal-style font** (Monaco) for tech aesthetic
- **Cyan accent colors** (#00d4ff) with professional styling
- **Dark theme** (#0f0f0f background) for low-light environments
- **Responsive grid layouts** that adapt from mobile to desktop
- **Interactive buttons** with hover effects and visual feedback
- **Real-time data display** with color-coded status indicators
- **Error handling** with user confirmations for destructive actions

### Key Technologies
- **Backend**: Flask, Threading, JSON API
- **Frontend**: HTML5, CSS3, Vanilla JavaScript (no frameworks)
- **Communication**: AJAX/Fetch API with JSON payloads
- **Styling**: CSS Custom Properties (variables) for easy theming

---

## Usage Guide

### Starting the System
```bash
cd /home/jason/jct
python main.py
```

The web server starts automatically and listens on `http://localhost:5000`

### Accessing the Interface
1. Open a browser
2. Navigate to `http://<raspberry_pi_ip>:5000`
3. The dashboard loads with current system status
4. All data auto-refreshes on button interactions

### Common Tasks

**Take a Photo:**
1. Click "CAPTURE PHOTO" button
2. Wait 5 seconds for capture to complete
3. Photo appears in the Live Feed section

**Control Lights with Duration:**
1. Enter duration in seconds in the input field
2. Click "ON" to turn on for that duration
3. Click "OFF" to turn off immediately

**Monitor System Health:**
1. Click "PI HEALTH" in Manual Control section
2. View CPU temperature, RAM usage, Disk space, Uptime
3. Status updates every action

**Emergency Stop:**
1. Scroll to System Control section
2. Click "EMERGENCY STOP"
3. Confirm the prompt
4. All operations halt immediately

---

## UI Components

### Color Scheme
```
Primary Background:  #0f0f0f (near black)
Panel Background:    #1a1a1a (dark gray)
Accent Color:        #00d4ff (cyan)
Success:             #00ff41 (bright green)
Error:               #ff3333 (red)
Warning:             #ffaa00 (amber)
Text:                #e0e0e0 (light gray)
Borders:             #333 (medium gray)
```

### Button Styles
- **Blue** - Primary actions (CAPTURE, SYNC)
- **Green** - Safe actions (ON, PLAY)
- **Red** - Destructive (OFF, STOP, EMERGENCY)
- **Yellow** - Important (FULL SENSOR SWEEP)
- **Gray** - Secondary (Groups, Utilities)
- **Outline** - Tertiary (Ping commands, Tracks)

### Responsive Design
- Desktop (1400px): 4-column grids
- Tablet (768px): 2-column grids
- Mobile: Single column with stacked elements

---

## Data Flow

```
User Clicks Button
    ↓
JavaScript Fetch → POST to API
    ↓
Flask Route Handler
    ↓
Controller/Scheduler Method
    ↓
Hardware Operation
    ↓
Page Reload (300ms delay)
    ↓
Dashboard Updates with New Data
```

---

## Files Modified/Created

1. **templates/index.html** - Complete web interface
   - 583 lines of HTML, CSS, JavaScript
   - Fully responsive design
   - All features integrated

2. **aerosense/interface/web.py** - Already existed
   - API endpoints fully functional
   - Flask app ready to serve

3. **aerosense/config/settings.py** - Configuration reference
   - Hardware paths and timeouts
   - Sensor intervals

---

## Advanced Features

### Keyboard Shortcuts
- **Alt+R** - Refresh page
- **Alt+S** - Quick stop (extensible)

### Auto-Features
- Page auto-refreshes on API calls
- Data auto-updates displayed timestamps
- Real-time cache monitoring

### Error Handling
- Connection error alerts
- Confirmation dialogs for dangerous operations
- Graceful failure messages

---

## Browser Compatibility
- Chrome/Chromium: ✅ Full support
- Firefox: ✅ Full support
- Safari: ✅ Full support
- Edge: ✅ Full support
- Mobile browsers: ✅ Responsive design

---

## Future Enhancement Ideas
1. WebSocket support for real-time updates
2. Charts/graphs for historical data
3. User authentication
4. System log viewer
5. Schedule builder interface
6. Photo gallery with timestamps
7. Alert notifications
8. Exported data analytics

---

## Support & Troubleshooting

**Web server won't start:**
- Check if port 5000 is available
- Verify Flask is installed
- Check logs in `/tmp/aerosense.log`

**Buttons not responding:**
- Verify Arduino connection
- Check system logs
- Try "SYNC STATE" to resync

**Styling looks broken:**
- Clear browser cache (Ctrl+Shift+Delete)
- Try different browser
- Check if CSS loaded (F12 → Network tab)

---

**Created:** January 26, 2026  
**Version:** 1.0.0  
**Status:** Production Ready ✅
