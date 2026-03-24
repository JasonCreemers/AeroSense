# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

- Clean up startup
    ((.venv) ) aerosense@aerosense:~/aerosense_prod $ cd /home/aerosense/aerosense_prod && source .venv/bin/activate && python3 -m aerosense.main

=== AEROSENSE GARDEN CONTROLLER v4.3.2 | (2026-03-24) ===
[15:34:21] AeroSense.Main - INFO: System initializing...
[15:34:21] AeroSense.Hardware.Arduino - INFO: Connecting to Arduino on /dev/ttyACM0 (Attempt 1/3)...
[15:34:23] AeroSense.Hardware.Arduino - INFO: Serial connection established.
[15:34:23] AeroSense.Hardware.Arduino - INFO: Serial listener thread started.
[15:34:26] AeroSense.ML.Health - INFO: Health model loaded successfully.
[15:34:26] AeroSense.Core.Controller - INFO: Startup Safety: Sent preemptive STOP to hardware.
[15:34:26] AeroSense.Core.Controller - INFO: System Controller Initialized.
[15:34:26] AeroSense.Core.Controller - INFO: Syncing state with Hardware...
[15:34:26] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:PUMP_OFF
[15:34:26] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:LIGHTS_OFF
[15:34:26] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:MUSIC_STOP
[15:34:26] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:EMERGENCY_STOP
[15:34:27] AeroSense.Core.Controller - INFO: State Sync Complete.
[15:34:27] AeroSense.Core.Controller - INFO: Music Request: GRANTED
>> 23 days remain until Senior Design Day is here. Godspeed.
[15:34:27] AeroSense.Core.Scheduler - INFO: Scheduler Initialized. All cycles standing by.
[15:34:27] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:MUSIC_STOP
[15:34:27] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:PLAY_SONG,Granted

[CLI] Ready. Type 'HELP' for commands.

[15:34:27] AeroSense.Main - INFO: System Active.
[15:34:27] AeroSense.Hardware.Arduino - INFO: ARDUINO: ACK:MUSIC_STOP
[15:34:27] AeroSense.Hardware.Arduino - CRITICAL: HARDWARE ALERT: ALERT:SONG_COMPLETE


- Implement MOSS.
    - Utilize Ollama as the framework and maybe Gemma as the model. Give it access to several tools to control the overall system. Have it be able to talk through the CLI or through the GUI. Give it personality. Give it LEDS to control its thinking
    - Tools: Read any of the .md files, Make a new plant health file, Have it read the machine learning outputs, Have it run the sensors, Have it run the machine learning, Have it read the system intervals and times.
    - Outputs: Can inform you of overall system health, suggested changes to system intervals and times, Anything else plant related.

- README.md full revamp.

---

## Upcoming Tasks

---

## Long Term Tasks

---