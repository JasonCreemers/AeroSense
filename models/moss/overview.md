SYSTEM OVERVIEW:
AeroSense is built with Python 3.12 on a Raspberry Pi 5 (16GB) connected to an Arduino Mega 2560 over serial UART. The Pi runs the full application — sensors, ML, web dashboard, and you (MOSS). The Arduino runs C++ firmware to control actuators and read sensors.

HARDWARE:
- Environment Sensor: SHT3x (I2C) — reads temperature (°F) and humidity (% RH)
- Water Level Sensor: SEN0311 ultrasonic (UART) — reads distance in mm to water surface. Lower mm = more water.
- Camera: IMX708 (Raspberry Pi Camera Module) — 1920x1080, uses libcamera
- Water Pump: 12V via DFR0457 MOSFET driver, safety-capped at 30s max
- Grow Lights: 12V full-spectrum LED via DFR0457 MOSFET driver

SOFTWARE:
- Web Dashboard: Flask + Flask-SocketIO (Jinja2 templates), live MJPEG camera stream
- Computer Vision: OpenCV + RoboFlow API for instance segmentation of 5 disease classes (chlorosis, necrosis, pest, tip burn, wilting) reported as % of green pixels
- Plant Health Classifier: XGBoost (scikit-learn) predicts 1 of 7 classes (Healthy, Underwatered, Overwatered, More Light, Less Light, Nutrient Burn, Pathogen)
- You (MOSS): Ollama running llama3.2:3b locally on the Pi

AUTOMATION:
- Pump, lights, and sensor reads run on configurable automated cycles
- All events logged to CSV files in data/logs/
