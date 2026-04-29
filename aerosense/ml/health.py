"""
AeroSense Plant Health Classifier.

This module provides XGBoost-based plant health classification.
It computes 16 engineered features from vision, environment, water level,
and light log data, then predicts one of 7 health classes.
"""

import csv
import logging
import math
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from config import settings


# Feature names in ROADMAP order (must match training script)
FEATURE_NAMES: List[str] = [
    "chlorosis_ratio", "decay_ratio", "tip_burn_ratio", "pest_density",
    "wilting_ratio", "growth_velocity", "instant_temp", "delta_temp",
    "temp_slope", "instant_humidity", "instant_vpd", "vpd_shock",
    "water_volume", "light_interval", "time_of_day_x", "time_of_day_y",
]


class HealthClassifier:
    """
    Performs plant health classification using a pre-trained XGBoost model.

    Attributes:
        log (logging.Logger): Dedicated logger for health operations.
        model: The loaded XGBClassifier instance, or None if unavailable.
        label_encoder: The loaded LabelEncoder for class mapping, or None.
        feature_names (list): Ordered feature names the model expects.
    """

    def __init__(self):
        """Initialize the HealthClassifier and attempt to load the model."""
        self.log = logging.getLogger("AeroSense.ML.Health")
        self.model = None
        self.label_encoder = None
        self.feature_names: List[str] = FEATURE_NAMES
        self._load_model()

    def _load_model(self) -> bool:
        """
        Load the XGBClassifier, LabelEncoder, and feature names from pickle.

        The pickle file contains a dict with keys: "model", "encoder", "features".

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        model_path = settings.HEALTH_MODEL_PATH

        if not model_path.exists():
            self.log.warning(f"Health model not found at {model_path}. Predictions disabled.")
            return False

        try:
            with open(model_path, "rb") as f:
                bundle = pickle.load(f)

            self.model = bundle["model"]
            self.label_encoder = bundle["encoder"]
            loaded_features = bundle["features"]

            # Validate feature count matches expected
            if len(loaded_features) != len(FEATURE_NAMES):
                self.log.error(
                    f"Feature count mismatch: model has {len(loaded_features)}, "
                    f"expected {len(FEATURE_NAMES)}. Re-run scripts/train_health.py."
                )
                self.model = None
                self.label_encoder = None
                return False

            self.feature_names = loaded_features
            self.log.info("Health model loaded successfully.")
            return True

        except Exception as e:
            self.log.error(f"Failed to load health model: {e}. Try re-running scripts/train_health.py.")
            self.model = None
            self.label_encoder = None
            return False

    def compute_features(self, vision_data: dict, env_data: tuple, log_dir: Path) -> Optional[Dict[str, float]]:
        """
        Compute all 16 features from current sensor readings and CSV history.

        Args:
            vision_data (dict): Result from run_vision_analysis() containing
                green_pixels (int) and class_pixels (dict).
            env_data (tuple): (temp_f, humidity_rh) from read_environment().
            log_dir (Path): Directory containing CSV log files.

        Returns:
            Optional[Dict[str, float]]: Feature name → value mapping, or None on failure.
        """
        try:
            green_px = vision_data.get("green_pixels", 0)
            class_px = vision_data.get("class_pixels", {})
            temp_f, humidity_rh = env_data

            # --- Vision Ratios (features 1-5) ---
            chlorosis_ratio = self._safe_ratio(class_px.get("chlorosis", 0), green_px)
            decay_ratio = self._safe_ratio(class_px.get("necrosis", 0), green_px)
            tip_burn_ratio = self._safe_ratio(class_px.get("tip_burn", 0), green_px)
            pest_density = self._safe_ratio(class_px.get("pest", 0), green_px)
            wilting_ratio = self._safe_ratio(class_px.get("wilting", 0), green_px)

            # --- Growth Velocity (feature 6) ---
            growth_velocity = self._compute_growth_velocity(log_dir)

            # --- Environment Features (features 7-12) ---
            instant_vpd = self._compute_vpd(temp_f, humidity_rh)
            env_features = self._compute_env_features(temp_f, humidity_rh, instant_vpd, log_dir)

            # --- Water Volume (feature 13) ---
            water_volume = self._compute_water_volume(log_dir)

            # --- Light Interval (feature 14) ---
            light_interval = self._compute_light_interval(log_dir)

            # --- Time Encoding (features 15-16) ---
            now = datetime.now()
            hour_frac = now.hour + now.minute / 60.0
            time_of_day_x = math.sin(2 * math.pi * hour_frac / 24)
            time_of_day_y = math.cos(2 * math.pi * hour_frac / 24)

            features = {
                "chlorosis_ratio": chlorosis_ratio,
                "decay_ratio": decay_ratio,
                "tip_burn_ratio": tip_burn_ratio,
                "pest_density": pest_density,
                "wilting_ratio": wilting_ratio,
                "growth_velocity": growth_velocity,
                "instant_temp": temp_f,
                "delta_temp": env_features["delta_temp"],
                "temp_slope": env_features["temp_slope"],
                "instant_humidity": humidity_rh,
                "instant_vpd": instant_vpd,
                "vpd_shock": env_features["vpd_shock"],
                "water_volume": water_volume,
                "light_interval": light_interval,
                "time_of_day_x": time_of_day_x,
                "time_of_day_y": time_of_day_y,
            }

            # Sanitize: replace NaN/Inf with 0.0
            for key in features:
                val = features[key]
                if math.isnan(val) or math.isinf(val):
                    features[key] = 0.0

            return features

        except Exception as e:
            self.log.error(f"Feature computation failed: {e}")
            return None

    def predict(self, features: Dict[str, float]) -> Optional[Tuple[str, float]]:
        """
        Run XGBoost inference on computed features.

        Args:
            features (dict): Feature name → float mapping from compute_features().

        Returns:
            Optional[Tuple[str, float]]: (predicted_label, confidence_percent) or None if model unavailable.
        """
        if self.model is None or self.label_encoder is None:
            return None

        try:
            # Build feature array in the order the model expects
            feature_array = np.array([[features.get(name, 0.0) for name in self.feature_names]])

            # Validate feature count
            if feature_array.shape[1] != len(self.feature_names):
                self.log.error(f"Feature count mismatch: expected {len(self.feature_names)}, got {feature_array.shape[1]}")
                return None

            # Get class probabilities and pick the top prediction
            probabilities = self.model.predict_proba(feature_array)[0]
            top_index = int(np.argmax(probabilities))
            confidence = float(probabilities[top_index]) * 100.0
            label = str(self.label_encoder.inverse_transform([top_index])[0])

            return (label, confidence)

        except Exception as e:
            self.log.error(f"Prediction failed: {e}")
            return None

    # Internal Helpers

    def _safe_ratio(self, numerator: float, denominator: float) -> float:
        """Return numerator/denominator, or 0.0 if denominator is zero."""
        if denominator == 0:
            return 0.0
        return numerator / denominator

    def _compute_vpd(self, temp_f: float, humidity_rh: float) -> float:
        """
        Compute Vapor Pressure Deficit in kPa.

        Args:
            temp_f (float): Temperature in Fahrenheit.
            humidity_rh (float): Relative humidity percentage.

        Returns:
            float: VPD in kPa, clamped to >= 0.0.
        """
        temp_c = (temp_f - 32) * 5 / 9
        svp = 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        vpd = svp * (1 - humidity_rh / 100)
        return max(0.0, vpd)

    def _compute_growth_velocity(self, log_dir: Path) -> float:
        """
        Compute growth velocity from the last 2 vision log entries.

        Returns:
            float: Percentage change in green pixels, or 0.0 if insufficient data.
        """
        vision_path = log_dir / "vision_log.csv"
        rows = self._read_csv_tail(vision_path, n=2)

        if len(rows) < 2:
            return 0.0

        try:
            # Green_Pixels is column index 3 (Timestamp, Source_Image, Total_Pixels, Green_Pixels, ...)
            prev_green = float(rows[-2][3])
            cur_green = float(rows[-1][3])
            return self._safe_ratio(cur_green - prev_green, prev_green) * 100
        except (IndexError, ValueError):
            return 0.0

    def _compute_env_features(self, temp_f: float, humidity_rh: float,
                              instant_vpd: float, log_dir: Path) -> Dict[str, float]:
        """
        Compute delta_temp, temp_slope, and vpd_shock from env log history.

        Returns:
            dict with keys: delta_temp, temp_slope, vpd_shock.
        """
        result = {"delta_temp": 0.0, "temp_slope": 0.0, "vpd_shock": 0.0}

        env_path = log_dir / "env_log.csv"
        rows = self._read_csv_recent(env_path, hours=24)

        if not rows:
            return result

        # Parse temp and humidity values from rows
        temps = []
        vpds = []
        for row in rows:
            try:
                t = float(row[1])  # Temp_F
                h = float(row[2])  # Humidity_RH
                temps.append(t)
                vpds.append(self._compute_vpd(t, h))
            except (IndexError, ValueError):
                continue

        if temps:
            avg_temp = sum(temps) / len(temps)
            result["delta_temp"] = temp_f - avg_temp

        if len(temps) >= 2:
            # temp_slope: current reading vs the previous reading
            result["temp_slope"] = temp_f - temps[-2]

        if vpds:
            avg_vpd = sum(vpds) / len(vpds)
            result["vpd_shock"] = instant_vpd - avg_vpd

        return result

    def _compute_water_volume(self, log_dir: Path) -> float:
        """
        Compute net water consumed in the past 24 hours (mL).

        Uses water level distance readings: a drop in level = water consumed.
        Container area: 12in x 10.5in = 812.9 cm².

        Returns:
            float: Water volume in mL, or 0.0 if insufficient data.
        """
        water_path = log_dir / "water_log.csv"
        rows = self._read_csv_recent(water_path, hours=24)

        if len(rows) < 2:
            return 0.0

        try:
            earliest_mm = float(rows[0][1])   # Level_mm
            latest_mm = float(rows[-1][1])     # Level_mm

            # Distance increases = water level dropped = water consumed
            delta_mm = latest_mm - earliest_mm
            if delta_mm < 0:
                delta_mm = 0.0  # Pump refilled more than consumed

            # Convert mm drop to mL: area_cm2 * (delta_mm / 10)
            volume_ml = settings.CONTAINER_AREA_CM2 * (delta_mm / 10)
            return volume_ml

        except (IndexError, ValueError):
            return 0.0

    def _compute_light_interval(self, log_dir: Path) -> float:
        """
        Compute total hours of light delivered in the past 24 hours.

        Parses ON/OFF events from lights_log.csv and pairs them.
        Duration_Sec column is unreliable (scheduler logs 0 for indefinite),
        so we compute actual durations from timestamp pairs.

        Returns:
            float: Total light hours, or 0.0 if no data.
        """
        lights_path = log_dir / "lights_log.csv"
        rows = self._read_csv_recent(lights_path, hours=24)

        if not rows:
            return 0.0

        now = datetime.now()
        window_start = now - timedelta(hours=24)
        total_seconds = 0.0
        last_on_time = None
        first_event = True

        for row in rows:
            try:
                ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                action = row[1].strip().upper()
            except (IndexError, ValueError):
                continue

            if action == "ON":
                first_event = False
                if last_on_time is None:
                    last_on_time = ts
            elif action == "OFF":
                if last_on_time is not None:
                    total_seconds += (ts - last_on_time).total_seconds()
                    last_on_time = None
                elif first_event:
                    # Very first event is OFF — lights were on since window start
                    total_seconds += (ts - window_start).total_seconds()
                # else: duplicate OFF with lights already off — ignore
                first_event = False

        # If lights are still ON at the end of the window
        if last_on_time is not None:
            total_seconds += (now - last_on_time).total_seconds()

        return total_seconds / 3600.0

    def _read_csv_recent(self, path: Path, hours: int = 24) -> List[List[str]]:
        """
        Read CSV rows from the past N hours.

        Args:
            path (Path): Path to the CSV file.
            hours (int): How many hours back to include.

        Returns:
            List[List[str]]: Matching rows (excluding header), chronologically ordered.
        """
        if not path.exists():
            return []

        cutoff = datetime.now() - timedelta(hours=hours)
        results = []

        try:
            with open(path, "r", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header

                for row in reader:
                    if not row:
                        continue
                    try:
                        ts = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                        if ts >= cutoff:
                            results.append(row)
                    except (ValueError, IndexError):
                        continue
        except Exception:
            pass

        return results

    def _read_csv_tail(self, path: Path, n: int = 2) -> List[List[str]]:
        """
        Read the last N data rows from a CSV file (excluding header).

        Args:
            path (Path): Path to the CSV file.
            n (int): Number of tail rows to return.

        Returns:
            List[List[str]]: The last N rows, or fewer if file has less data.
        """
        if not path.exists():
            return []

        try:
            with open(path, "r", newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # Skip header

                # Keep a rolling buffer of the last N rows
                buffer = []
                for row in reader:
                    if row:
                        buffer.append(row)
                        if len(buffer) > n:
                            buffer.pop(0)
                return buffer
        except Exception:
            return []
