# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add sad Spongebob song.
- Add UA Fight Song
- Add UA Alma Mater

- Clean up Flask GUI.

- Implement armageddon countdown at initialization/good morning.

---

## Upcoming Tasks
- Implement additional redundant safety checks for lights and pump.
- Check all loops to make sure there are ending conditions for all of them.

- Implement better noise filtering for sensor data (moving averages, outlier rejection, etc.).

- CHECK WITH JOSIE: Implement logic for scheduler to interpret minutes as well as hours.

---

## Long Term Tasks

- MAYBE: Develop a web-based HTML dashboard for remote monitoring and control.

- Train a Computer Vision model to be used for plant health.
    - Utilize OpenCV to analyze the canopy for the number of green pixels (plant coverage).
    - Train an AI vision model using RoboFlow, with YoloV8n as the architecture and PyTorch as the engine. Calculate signs of stress on the plant (stress, yellowing, decay, browning, etc.).
    - Calculate a ratio for each class, and develop an algorithm for making system changes based on this ratio.
    - Link AI detection results to a mood system, have the system light up and play audio.

- LAST THING: Have an overall health checkup for the system. Have it run the model and inform you of actions that are needed (water level, nutrient concentration, temperature adjustments, etc.). Tie this back into a ChatGPT wrapper.