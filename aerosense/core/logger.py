"""
AeroSense Logger Module.

This module handles the centralization of system telemetry. 
It manages writing sensor data to CSV files and recording system-level events to the main status log.
"""

import csv
import logging
from pathlib import Path
import time
from typing import List, Any

from config import settings

class Logger:
    """
    Handles logging all sensor telemetry to CSV files and the system status log.

    Attributes:
        log_dir (Path): The directory where logs are stored.
        paths (Dict[str, Path]): A mapping of log keys to their Path objects.
        sys_log (logging.Logger): The dedicated logger instance for system events.
    """

    def __init__(self):
        """
        Initialize the Logger, create directories, and bootstrap CSV headers.
        """
        # Define file paths for specific logs
        self.log_dir: Path = settings.LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths
        self.paths: Dict[str, Path] = {
            "pump": self.log_dir / "pump_log.csv",
            "lights": self.log_dir / "lights_log.csv",
            "env": self.log_dir / "env_log.csv",
            "water": self.log_dir / "water_level_log.csv",
            "camera": self.log_dir / "camera_log.csv",
            "master": self.log_dir / "master_log.csv",
            "music": self.log_dir / "music_log.csv",
            "pi": self.log_dir / "pi_log.csv",
            "training": self.log_dir / "training_log.csv",
            "system": self.log_dir / "system_status.log"
        }

        # Setup general system logger
        self.sys_log = logging.getLogger("AeroSense.Core")

        # Ensure every log file exists with proper headers
        self._bootstrap_csv_files()

    def _bootstrap_csv_files(self):
        """
        Ensure every log file exists with a proper header row.
        If a file is missing, it creates it and writes the header.
        """
        headers = {
            "pump": ["Timestamp", "Action", "Duration_Sec"],
            "lights": ["Timestamp", "Action", "Duration_Sec"],
            "env": ["Timestamp", "Temp_F", "Humidity_RH"],
            "water": ["Timestamp", "Level_mm"],
            "master": ["Timestamp", "Temp_F", "Humidity_RH", "Water_Level_mm", "Image_Paths"],
            "camera": ["Timestamp", "Image_Paths"],
            "music": ["Timestamp", "Song_Title"],
            "pi": ["Timestamp", "CPU_Temp_C", "RAM_Usage_Pct", "Disk_Free_GB", "Uptime_Hours"],
            "training": ["Timestamp", "Tile_1", "Tile_2", "Tile_3", "Tile_4", "Tile_5", "Tile_6"]
        }

        # Check and create each CSV
        for key, header in headers.items():
            path = self.paths[key]

            # Only create the file if it doesn't exist
            if not path.exists():
                try:
                    with open(path, 'w', newline='', buffering=1) as f:
                        csv.writer(f).writerow(header)
                except IOError as e:
                    self.sys_log.error(f"Failed to bootstrap {key} log: {e}")
            
    def _get_timestamp(self) -> str:
        """
        Return current date and time in SQL-friendly format.

        Returns:
            str: Timestamp string (YYYY-MM-DD HH:MM:SS).
        """
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def _write_row(self, log_key: str, data: list):
        """
        Append a row to the specified CSV log file.

        Args:
            log_key (str): The key matching self.paths (e.g., 'pump', 'env').
            data (List[Any]): The list of values to append (excluding timestamp).
        """
        try:
            with open(self.paths[log_key], 'a', newline='', buffering=1) as f:
                # Prepend timestamp and write immediately
                csv.writer(f).writerow([self._get_timestamp()] + data)
        except Exception as e:
            # Catch IO errors
            self.sys_log.error(f"IO Error writing to {log_key}: {e}")

    # --- Telemetry API ---
    def log_alert(self, message: str) -> None:
        """
        Log a warning or critical event to the system status log.

        Args:
            message (str): The warning message to display.
        """
        self.sys_log.warning(f"ALERT: {message}")

    def log_pump(self, state: str, duration: int = 0) -> None:
        """
        Log a pump event.

        Args:
            state (str): 'ON' or 'OFF'.
            duration (int): Duration in seconds (default 0).
        """
        self._write_row("pump", [state.upper(), duration])
        self.sys_log.info(f"PUMP: {state.upper()} ({duration}s)")

    def log_lights(self, state: str, duration: int = 0) -> None:
        """
        Log a lighting event.

        Args:
            state (str): 'ON' or 'OFF'.
            duration (int): Duration in seconds (default 0).
        """
        self._write_row("lights", [state.upper(), duration])
        self.sys_log.info(f"LIGHTS: {state.upper()} ({duration}s)")

    def log_environment(self, temp_f: float, humidity: float) -> None:
        """
        Log environmental sensor readings.

        Args:
            temp_f (float): Temperature in Fahrenheit.
            humidity (float): Relative Humidity %.
        """
        self._write_row("env", [round(temp_f, 2), round(humidity, 2)])

    def log_water(self, level_mm: int) -> None:
        """
        Log water level readings.

        Args:
            level_mm (int): Distance to water surface in millimeters.
        """
        self._write_row("water", [level_mm])

    def log_camera(self, images: List[str]) -> None:
        """
        Log a camera capture event.

        Args:
            images (List[str]): A list of filenames for the captured images.
        """
        image_str = ";".join(images)
        self._write_row("camera", [image_str])
        self.sys_log.info(f"CAMERA: Saved {len(images)} files to log.")

    def log_master(self, temp: float, humidity: float, water: int, images: List[str]) -> None:
        """
        Record a synchronized system snapshot to the master dataset.

        Args:
            temp (float): The temperature reading in Fahrenheit.
            humidity (float): The relative humidity percentage.
            water (int): The distance to water surface in millimeters.
            images (List[str]): A list of file paths for the captured image sequence.
        """
        image_str = ";".join(images)
        
        row = [
            round(temp, 2), 
            round(humidity, 2), 
            water, 
            image_str
        ]
        self._write_row("master", row)

    def log_music(self, song_name: str) -> None:
        """
        Log a music playback event.

        Args:
            song_name (str): Title of the song or note played.
        """
        self._write_row("music", [song_name])

    def log_pi_stats(self, temp: float, ram: float, disk: float, uptime: float) -> None:
        """
        Log comprehensive system health stats.

        Args:
            temp (float): CPU Temperature in Celsius.
            ram (float): RAM Usage percentage.
            disk (float): Free Disk Space in GB.
            uptime (float): System Uptime in Hours.
        """
        self._write_row("pi", [temp, ram, disk, uptime])

    def log_training(self, tile_filenames: List[str]) -> None:
        """
        Log a training image split event.

        Args:
            tile_filenames (List[str]): A list of 6 filenames for the split tiles.
        """
        self._write_row("training", tile_filenames)
        self.sys_log.info(f"TRAINING: Logged {len(tile_filenames)} tiles.")