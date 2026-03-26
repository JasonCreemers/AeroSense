# Product Roadmap

This document outlines the development trajectory for the AeroSense project. Tasks are prioritized by execution window: **Immediate**, **Upcoming**, and **Long Term**.

## Immediate Tasks
- Add UA Fight Song
- Add UA Alma Mater.

- MOSS possible changes
    - Remove ability to read .md files and just feed them all in every time
    - Remove ability to check temperature and distance, just feed in every time.
    - Only tool to have is to run plant health

---

## Upcoming Tasks

- GUI full revamp.
    - Have each box able to be dropped down or not.
    - Have new sliders and graphs and just better information and whatnot.
    - Have it more consistent.
    - Maybe make it like a situation monitoring webpage.

- README.md full revamp.

- Fine tune XGBoost model
    - Heavy weight on pixel ratios.
        - Chlorosis: above 1.5%
        - Necrosis: above 1%
        - Pest: above 0.2%
        - Tip burn: above 1%
        - Wilting: above 1%
    - Less of a focus on water volume, time x, and time y.
    - More focus on VPD
    - Less focus on temp/humidity.

---

## Long Term Tasks

---