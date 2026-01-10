# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add sad Spongebob song.

---

## Upcoming Tasks

### Serial Changes
- Clean up variable usage in `firmware.ino`.
- Rewrite firmware string handling to use C-style `char[]` arrays and `strtok` instead of `String` objects to prevent memory fragmentation.

### Actuation Changes
- Implement additional redundant safety checks for hardware actuators.

### Sensor Changes
- Implement better noise filtering for sensor data (moving averages/outlier rejection).
- Implement discrete logic for **High**, **Medium**, and **Low** water level alerts (currently binary).
- Add more direct Raspberry Pi control commands.

### Audio Changes
- Implement an **Octave Shifter** in `music.h` to expand note range.
- Add University of Akron "Fight Song" and "Alma Mater".
- Move randomization logic to Python (`controller.py`) and categorize songs into "Happy", "Sad", "Angry", etc. playlists.

---

## Long Term Tasks

### User Interface Changes
- Develop a local HTML GUI for direct control on the Raspberry Pi.
- Develop a web-based HTML dashboard for remote monitoring and control.

### MOSS Changes
- Train a **RoboFlow** Computer Vision model for plant health.
- Implement **YOLO** architecture for object/growth detection.
- Train AI model to make system changes based on readings and feedback.
- Link AI detection results to the audio system.