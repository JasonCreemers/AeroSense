# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

- Implement the XGBoost health modifier.
    - Implement a XGBClassifier using XGBoost. Have it take in several inputs from the csv and make a determination of the overal plant health. Train this on synthetic data initially.
    - Inputs: Chlorosis Ratio, Decay Ratio, Wilting Ratio, Pest Density, Growth Velocity, Instant Temp, Delta Temp, Temp Slope, Instant Humidity, Instant VPD, VPD Shock, Water Volume, Light Interval, Time of Day X, Time of Day Y
    - Classes: Homeostasis, Hydric Stress, Hypoxia, Heat Stress, Nutrient Burn, Pathogen/Pest

- Implement MOSS.
    - Utilize Ollama as the framework and maybe Gemma as the model. Give it access to several tools to control the overall system. Have it be able to talk through the CLI or through the GUI. Give it personality. Give it LEDS to control its thinking
    - Tools: Read any of the .md files, Make a new plant health file, Have it read the machine learning outputs, Have it run the sensors, Have it run the machine learning, Have it read the system intervals and times.
    - Outputs: Can inform you of overall system health, suggested changes to system intervals and times, Anything else plant related.

- README.md full revamp.
    - New machine learning section.

---

## Upcoming Tasks

---

## Long Term Tasks

---