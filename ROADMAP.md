# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Double check 3.2.0 FIRST
- Add GUI command to help list

- FLASK GUI
    - FEED SECTION. Have a window showing most recent photo taken (Include time since taken somewhere). Have two buttons, one to run a capture sequence (RUN CAM) with just the standard amount of photos and one to open a indefinite live feed (RUN LIVE CAM). 
    - CYCLES SECTION. Have a button for: PUMP, LIGHTS, ENVIRONMENT, WATER LEVEL, CAMERA, PI HEALTH. They should be toggleable, so when pressed the cycle is on and when pressed again cycle is off. Have it be clear whether they are pressed or not. At the top include buttons for SYSTEM, HARDWARE, SENSORS. These buttons are not toggleable, what they do is turn on all the respective cycles in their groups. If all the respective cycles in their groups are already on, then they turn them all off. Of course if the system is synced and one of these was off, they should be corrected.
    - RUN SECTION. Have a button for LIGHTS ON and a button for LIGHTS OFF. Next to LIGHTS ON, have a text box to put in a time, if left blank assume 0 and indefinite. Same for PUMP ON AND PUMP OFF. Also have buttons for RUN SENSORS, RUN ENVIRONMENT, RUN WATER LEVEL, RUN PI HEALTH. Next to Environment, water level, and pi health have the most recent data as well as the time since last taken next to it. 
    - AUDIO SECTION. Have a button for MUSIC PLAY RANDOM, and a button for MUSIC STOP. Also have a button for MUSIC PLAY with a text box next to it that allows the user to input a song. Can we also have the Music List on here?
    - DIAGNOSTICS SECTION. Have the output from the most recent RUN SENSORS and their results (Include time since taken below). Have buttons for STATUS, SYNC, RESET. PING SYSTEM, PING HARDWARE, PING PUMP, PING LIGHTS, PING SENSORS, PING ENVIRONMENT, PING WATER LEVEL, PING CAM, PING BUZZER. next to the pings for pump, lights, sensors, environment, water level, and cam have the results for the most recent ping as well as the time since it was pinged. The pings for system hardware and sensors should be at the top and ping their respective group similar to the cycles.
    - SYSTEM SECTION. Have buttons for STOP, EXIT.

- Add sad Spongebob song.
- Better way to list songs between `web.py` and also `controller/cli.py`

---

## Upcoming Tasks

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
- Develop a web-based HTML dashboard for remote monitoring and control.

### MOSS Changes
- Train a **RoboFlow** Computer Vision model for plant health.
- Implement **YOLO** architecture for object/growth detection.
- Train AI model to make system changes based on readings and feedback.
- Link AI detection results to the audio system.