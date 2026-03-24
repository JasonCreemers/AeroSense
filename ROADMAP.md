# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

- Cetner Plant health columns

- Add music buttons for each category (Happy, Angry, Sad, etc.)

- When hitting PING ALL on GUI, all the sensors get mixed up, like PUMP_OFF can appear under SYS.

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

---

## Upcoming Tasks

- Upgrade the system to a Pi 5 16GB. 
    - Need to figure out what to flash sd card to.
    - Install VSCode and Arduino IDE using the easy terminal installation.
    - Setup Git/GitHub with READ ONLY access to the terminal.
    - Need to set up Python 3.12 for use in the virtual environment. Set this up extremely carefully using the best method possible, maybe an official install from the python website or something? No ppa or deadsnakes only official debian or python or pi stuff.
    - Will need to resetup the virtual envrionment in the correct pathway.
    - Will need to configure to Raspberry Pi Connect.
    - Will need to configure the IMX708.
    - Will need to analyze what files will break or need updating, including all .md and all .py.

- Implement MOSS.
    - Framework: Implement an AI Agent (named MOSS) that you can chat with regarding the system. Have it frameworked by Ollama and choose a prebuilt model that will allow for fine tuning if needed (Maybe Gemma).
    - Purpose: This agent will have several prebuilt tools coded in Python that allow it to control the system, or inform the user of things going on within the system.
    - Interface: In the CLI, the user can type MOSS (Message). Any message begining with a Moss will be sent to the AI Agent, and an appropriate response will be sent back. Additionally, there will be a new chat box on the GUI, any message in here is automatically sent to the AI agent. Allow for a Agent Reset command that will kill the current conversation and start a new one.
    - Model: The model will have a based personality file. It will be informed of some of the general system capabilities, parameters, etc. However, we will also make some additional files to give it more knowledge on what is good and bad. Give it the ability to feel happy or sad and play music based on that and how plants are doing. It will also have some files regarding the users so it knows who we are.
    - Tools: Read any of the .md files to learn more about the system (Ex user asking about hardware, open hardware.md and read it). Read any of the model files (Ex user is asking about a user, read the file regarding the users.). Run the temp sensor. Run the distance sensor. Play any category of song (Ex when the model is happy play a random happy song). Run the vision command. Run the plant health command. Read the output of the vision command (maybe give it the ability to just read the relevant/most recent info from the .csv). Read the output of the plant health command (same as previous). Read the output of temp/dist (same as previous).
    - Outputs: It's purpose is to serve the user. It can offer suggestions based on what the output of the tools it has (Ex, plants need water, it reccomends increasing the water usage). It can also just provide information based on any of the model files or the .md files. It should be a fun companion that has its own distinct personality and is very helpful.
    - Need to be implemented as industry standard as possible. Think of all possible errors and edge cases. I am not set on this, willing to consider something else if a good argument is made. Must be coded simplely to allow for easy fine tuning, additional tools, and additional parameters. Should be stored in the ml folder with a new agent.py for the python, and have the model files stored in models folder.

- GUI full revamp.
    - Have each box able to be dropped down or not.
    - Have new sliders and graphs and just better information and whatnot.
    - Have it more consistent.
    - Maybe make it like a situation monitoring webpage.

- README.md full revamp.

---

## Long Term Tasks

---