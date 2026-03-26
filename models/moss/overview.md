# AeroSense System Overview

AeroSense is an automated aeroponic indoor garden built as a Senior Design project at the University of Akron.

## Architecture
- **Raspberry Pi 5 (16GB):** Runs Python application — sensors, camera, ML, web server, and MOSS.
- **Arduino Mega 2560:** Controls actuators (water pump, grow lights, buzzer) and reads sensors (environment, water level).
- Communication: Serial UART at 115200 baud.

## Sensors
- **Environment (DHT22):** Temperature (°F) and humidity (% RH). I2C address 0x44.
- **Water Level (Ultrasonic):** Distance in mm. Lower = more water. Over 100mm = critically low.

## Actuators
- **Water Pump:** 12V, safety-capped at 30s max runtime. Won't run if water is critically low.
- **Grow Lights:** 12V full-spectrum LED. Scheduled on/off by time of day.

## ML Pipelines
- **Vision:** 12MP camera captures image, splits into tiles, analyzes for 5 disease classes (chlorosis, necrosis, pest, tip_burn, wilting) plus green coverage.
- **Plant Health:** XGBoost classifier uses vision + sensor features to predict 7 health classes (Healthy, Underwatered, Overwatered, More_Light, Less_Light, Nutrient_Burn, Pathogen).

## Automation
- Pump, lights, and sensor reads run on configurable automated cycles.
- All events are logged to CSV files in data/logs/.
