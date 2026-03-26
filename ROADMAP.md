# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight song
- Add UA Alma Mater.
- Add another happpy song.
- Add another angry song.
- Add another sad song.
- Add another serious song.

---

## Upcoming Tasks

- Fine tune XGBoost model
    - Lets modify script.py to continue fine tuning the xgbclassifier model. We will keep all the relevant inputs and classes, but just continue to fine tune appropriately. 
    - Have a very heavy weight on the pixel ratios. For the below, note that "Good" is as expected, "Watchout" is it may mean something or may not. "Attention" is this is big issues.
        - Chlorosis: 0-0.5 good, 0.5-1.5 watchout, 1.5-3+ attention
        - Necrosis: 0-0.5 good, 0.5-1.5 watchout, 1.5-3+ attention
        - Pest: 0-0.1 good, 0.1-0.3 watchout, 0.3-0.5+ attention
        - Tip burn: 0-0.5 good, 0.5-1 watchout, 1-2+ attention
        - Wilting: 0-0.5 good, 0.5-1.5 watchout, 1.5-3+ attention
    - Include more of a focus on the instantaneous VPD (Use expected values from resaerch on what is good vs not good). 
    - Less of a focus (but still some) on instant temperature, humidity, and light
    - Put very very little focus on time x, time y, water
    - Make the appropriate determinations for how much of each of these affects the 7 classes and what is relevant vs non relevant.

- README.md full revamp.

---

## Long Term Tasks

---