# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

- Implement a XGBoost health determination tool.
    - Implement a XGBClassifier using XGBoost. Have a new command RUN PLANT HEALTH that runs the XGBClassifier. I assume we need a new .py file in the ml folder. when I run this, I want it to first run the RUN VISION command to get some fresh new information. Then, I want to have the following inputs as below. The ratios should come from the vision command it just ran, calculating appropirately (remember, the vision command stores those pixels in a csv). For the inputs that need previous data, if there is none available (i.e. it is the begining of the csv) just assume the value is the same, so the input is 1 or 100. It will also need to read the temperature and humidity data, so it should RUN TEMP as well. Some of these need a 24 hour average of temperature data, so if there is not enough csv logs or whatnot again, assume the average value is the same so the delta will be 0 or whatever respectively. Also, you will need to calculate VPD, the averafe VPD for the past 24 hours, so find the correct equations for those depending on the temp/humidity data we have. Also, you will need to read the dist csv to determinethe water volume in the past 24 hours. (the container is 12inx10.5in so do the math depending on the cm the dist has gone down). again if no readings then aassume its 0 water volume. also you will need to read the light log to find how much light has been delivered in the past 24 hours (they may have been turned off or on a few times). lastly, you need to calculate time x and time y (i reccomended some equations). Obviously, there are a lot of calculations here so if you have any questions whatsoever, feel free to ask. Once it runs through the XGBclsasifier and gets an output, then output that to the terminal. Make a new .csv log which stores first the date/time, then all the inputs in the order we have listed, then the classified output. We will want to train this on a synthetic dataset on my pc first, and then the pi will just have the weights, I beleive as just a pickle file if I'm not mistaked. I am likely not doing this the best way and likely forgot a few things, so if you have any questions please do not hesitate to ask I want this to be good good. I am also not set on the inputs or how they are calculated, I can be convinced to change them if a good argument is made, maybe look into that a bit. I am also not set on the classes so look into that I am willing to change if a good argument is made. The tricky part will be thinking of and handling all errors and edge cases, so be very very careful. Also make a good and thoughtful plan for how to implement this synthetic data. When I run the command. I just want it to output the classifier> Similarly, we should have a button on the GUI in a new box under Live Feed named MOSS for now. When pressed, just output the classifier. Also keep in mind any packages or dependencies we're gonna need. Read all .py files to ensure nothing else will break. Also come up with distinctive inputs for all classes.
    - Inputs: Chlorosis Ratio (chlorosis pixels/green pixels), Decay Ratio (necrosis pixels/green pixels), Tip Burn Ratio (tip burn pixels/green pixels), Pest Density(pest pixels/green pixels), Wilting Ratio (wilting pixels/green pixels),  Growth Velocity ((current green pixels - old green pixels)/old green pixels *100), Instant Temp (current temp reading), Delta Temp (current temp reading - (the average of the past 24 hours of temp readings)), Temp Slope (current temp - old temp), Instant Humidity (current humidirty), Instant VPD (current vapor pressure defecit), VPD Shock (current vpd - 24 hour vpd shock), Water Volume (24hr amount of water delivered), Light Interval (24 hour amount of light delivered), Time of Day X (sin(2pi(hour/24))), Time of Day Y(cos(2pi(hour/24)))
    - Classes: Homeostasis (healthy), Hydric Stress (underwatered), Hypoxia (overwatered), Heat Stress (environment too hot/dry), Light Stress (too much light), Nutrient Burn (nutrients too concentrated), Pathogen/Pest (plants have disease or pest)

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