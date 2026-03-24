"""
AeroSense Configuration Settings.

This module acts as the central repository for all global system configurations.
It defines parameters for serial communication, file system paths, automation schedules, and hardware configuration.

Usage:
    Import this module to access global settings:
    >>> from config import settings
    >>> print(settings.SERIAL_PORT)
"""

import os
from datetime import date
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv
load_dotenv()

# --- Serial Communication Configuration ---
# Use env var 'AEROSENSE_PORT' to override hardware defaults
SERIAL_PORT: str = os.getenv("AEROSENSE_PORT", "/dev/ttyACM0")
BAUD_RATE: int = 115200
SERIAL_TIMEOUT: int = 2
MAX_RETRIES: int = 3

# --- File System Paths ---
BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path = BASE_DIR / "data"
LOG_DIR: Path = DATA_DIR / "logs"
IMG_DIR: Path = DATA_DIR / "images"
TILES_DIR: Path = DATA_DIR / "tiles"
VISION_DIR: Path = DATA_DIR / "vision"
TILED_VISION_DIR: Path = DATA_DIR / "tiled_vision"

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)
TILES_DIR.mkdir(parents=True, exist_ok=True)
VISION_DIR.mkdir(parents=True, exist_ok=True)
TILED_VISION_DIR.mkdir(parents=True, exist_ok=True)

# --- Hardware Automation Schedules ---
# Pump Logic
PUMP_INTERVAL_MINS: int = 30
PUMP_DURATION_SEC: int = 10

# Lighting Logic
LIGHTS_START_HOUR: int = 10
LIGHTS_END_HOUR: int = 16

# Sensor Logic
SENSOR_INTERVAL_MINS: int = 30 

# --- Hardware Configuration ---
# Pump
PUMP_MAX_DURATION_SEC: int = 30 # Pump safety cutoff
PUMP_SAFETY_THRESHOLD_MM: int = 100 # Minimum water level (Empty is 150-180mm)
PUMP_SAFETY_INTERVAL_SEC: float = 2.0 # Interval between pump safety checks

# Lights
LIGHTS_MAX_DURATION_SEC: int = 86400 # Lights safety cutoff (24 hours)

# --- Camera Configuration ---
# Camera
CAM_BURST_COUNT: int = 1
CAM_RESOLUTION: Tuple[int, int] = (1920, 1080)
CAM_ROTATION: int = 0
CAM_VFLIP: bool = False

# --- Computer Vision ---
VISION_MODEL_ID: str = "moss-4nrjw/2"
VISION_CONFIDENCE: float = 0.50
VISION_CLASSES: list = ["chlorosis", "necrosis", "pest", "tip_burn", "wilting"]
VISION_GREEN_LOWER: tuple = (35, 40, 40)
VISION_GREEN_UPPER: tuple = (85, 255, 255)

# --- Plant Health Classifier ---
MODELS_DIR: Path = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
HEALTH_MODEL_PATH: Path = MODELS_DIR / "health_model.pkl"
HEALTH_CLASSES: list = [
    "Healthy", "Underwatered", "Overwatered",
    "More_Light", "Less_Light", "Nutrient_Burn", "Pathogen"
]
CONTAINER_AREA_CM2: float = 30.48 * 26.67  # 12in x 10.5in = 812.9 cm²

# --- Birthdays ---
BIRTHDAYS = [
    (1, 1, "MOSS"),
    (REDACTED),
    (REDACTED),
    (REDACTED),
    (REDACTED),
    (REDACTED)
]

# --- Countdown Configuration ---
COUNTDOWN_TARGET_DATE: date = date(2026, 4, 16)
COUNTDOWN_MSG_BEFORE: str = "{days} days remain until Senior Design Day is here. Godspeed."
COUNTDOWN_MSG_TODAY: str = "Today's the day, carpe diem people."
COUNTDOWN_MSG_AFTER: str = "You may rest now."