"""
AeroSense Health Model Training Script.

Generates synthetic training data and trains an XGBClassifier for plant health
classification. Outputs a pickle file containing the model, label encoder, and
feature names for deployment to the Raspberry Pi.

Usage (run from project root):
    python scripts/train_health.py

To tune the model, edit the CONFIGURATION section below and re-run.
"""

import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier


# ============================================================
# CONFIGURATION — Edit these to tune synthetic data & training
# ============================================================

SAMPLES_PER_CLASS = 500
NOISE_RATIO = 0.05          # Gaussian noise as fraction of range width
TEST_SPLIT = 0.2
RANDOM_SEED = 42
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "models" / "health_model.pkl"

FEATURE_NAMES = [
    "chlorosis_ratio", "decay_ratio", "tip_burn_ratio", "pest_density",
    "wilting_ratio", "growth_velocity", "instant_temp", "delta_temp",
    "temp_slope", "instant_humidity", "instant_vpd", "vpd_shock",
    "water_volume", "light_interval", "time_of_day_x", "time_of_day_y",
]

# Per-class feature ranges: {class_name: {feature: (low, high)}}
# To add/remove a class: add/remove a key here.
# To change a range: edit the (low, high) tuple.
# Features marked with # KEY are the primary distinguishing features for that class.
CLASS_PROFILES = {
    "Healthy": {
        "chlorosis_ratio":  (0.00, 0.02),   # KEY — very low
        "decay_ratio":      (0.00, 0.01),   # KEY — very low
        "tip_burn_ratio":   (0.00, 0.01),
        "pest_density":     (0.00, 0.01),
        "wilting_ratio":    (0.00, 0.02),
        "growth_velocity":  (2, 8),          # KEY — positive growth
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (55, 70),
        "instant_vpd":      (0.8, 1.2),
        "vpd_shock":        (-0.2, 0.2),
        "water_volume":     (50, 150),
        "light_interval":   (5, 7),
        "time_of_day_x":    (-1, 1),         # uniform (cyclical encoding)
        "time_of_day_y":    (-1, 1),         # uniform (cyclical encoding)
    },
    "Underwatered": {
        "chlorosis_ratio":  (0.05, 0.20),
        "decay_ratio":      (0.02, 0.10),
        "tip_burn_ratio":   (0.00, 0.03),
        "pest_density":     (0.00, 0.02),
        "wilting_ratio":    (0.10, 0.35),    # KEY — high wilting
        "growth_velocity":  (-15, -3),       # KEY — strong negative growth
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (30, 45),        # KEY — low humidity
        "instant_vpd":      (1.5, 2.5),     # KEY — high VPD
        "vpd_shock":        (0.3, 1.0),
        "water_volume":     (0, 30),         # KEY — very low water
        "light_interval":   (5, 7),
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
    "Overwatered": {
        "chlorosis_ratio":  (0.03, 0.15),
        "decay_ratio":      (0.05, 0.20),   # KEY — high decay
        "tip_burn_ratio":   (0.00, 0.02),
        "pest_density":     (0.00, 0.02),
        "wilting_ratio":    (0.05, 0.15),
        "growth_velocity":  (-10, 0),
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (80, 95),        # KEY — high humidity
        "instant_vpd":      (0.1, 0.5),     # KEY — very low VPD
        "vpd_shock":        (-0.5, -0.1),
        "water_volume":     (200, 500),      # KEY — very high water
        "light_interval":   (5, 7),
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
    "More_Light": {
        "chlorosis_ratio":  (0.10, 0.30),   # KEY — high chlorosis (pale)
        "decay_ratio":      (0.00, 0.03),
        "tip_burn_ratio":   (0.00, 0.02),
        "pest_density":     (0.00, 0.02),
        "wilting_ratio":    (0.03, 0.10),
        "growth_velocity":  (-12, -2),       # KEY — negative growth
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (55, 70),
        "instant_vpd":      (0.8, 1.2),
        "vpd_shock":        (-0.2, 0.2),
        "water_volume":     (50, 150),
        "light_interval":   (0, 3),          # KEY — very low light
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
    "Less_Light": {
        "chlorosis_ratio":  (0.08, 0.25),   # KEY — high chlorosis (photobleaching)
        "decay_ratio":      (0.01, 0.05),
        "tip_burn_ratio":   (0.01, 0.05),
        "pest_density":     (0.00, 0.02),
        "wilting_ratio":    (0.03, 0.10),
        "growth_velocity":  (-12, -2),       # KEY — negative growth
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (55, 70),
        "instant_vpd":      (0.8, 1.2),
        "vpd_shock":        (-0.2, 0.2),
        "water_volume":     (50, 150),
        "light_interval":   (10, 18),        # KEY — very high light
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
    "Nutrient_Burn": {
        "chlorosis_ratio":  (0.02, 0.10),
        "decay_ratio":      (0.03, 0.15),
        "tip_burn_ratio":   (0.10, 0.35),   # KEY — very high tip burn (unique)
        "pest_density":     (0.00, 0.02),
        "wilting_ratio":    (0.02, 0.08),
        "growth_velocity":  (-3, 3),
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (55, 70),
        "instant_vpd":      (0.8, 1.2),
        "vpd_shock":        (-0.2, 0.2),
        "water_volume":     (80, 200),
        "light_interval":   (5, 7),
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
    "Pathogen": {
        "chlorosis_ratio":  (0.01, 0.08),
        "decay_ratio":      (0.05, 0.25),   # KEY — high decay
        "tip_burn_ratio":   (0.00, 0.03),
        "pest_density":     (0.10, 0.40),   # KEY — very high pest density (unique)
        "wilting_ratio":    (0.03, 0.12),
        "growth_velocity":  (-8, 0),
        "instant_temp":     (68, 78),
        "delta_temp":       (-2, 2),
        "temp_slope":       (-1, 1),
        "instant_humidity": (70, 90),
        "instant_vpd":      (0.3, 0.8),
        "vpd_shock":        (-0.3, 0.1),
        "water_volume":     (50, 150),
        "light_interval":   (5, 7),
        "time_of_day_x":    (-1, 1),
        "time_of_day_y":    (-1, 1),
    },
}

XGB_PARAMS = {
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "objective": "multi:softmax",
    "eval_metric": "mlogloss",
    "random_state": RANDOM_SEED,
}

# ============================================================
# END CONFIGURATION
# ============================================================


def generate_synthetic_data() -> pd.DataFrame:
    """
    Generate labeled synthetic data from CLASS_PROFILES config.

    For each class, samples are drawn uniformly from the defined ranges,
    then Gaussian noise is added (scaled by NOISE_RATIO * range_width).

    Returns:
        pd.DataFrame: DataFrame with feature columns + 'label' column.
    """
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []

    for class_name, profile in CLASS_PROFILES.items():
        for _ in range(SAMPLES_PER_CLASS):
            sample = {}
            for feat in FEATURE_NAMES:
                low, high = profile[feat]
                value = rng.uniform(low, high)

                # Add Gaussian noise
                range_width = high - low
                if range_width > 0:
                    noise = rng.normal(0, NOISE_RATIO * range_width)
                    value += noise

                sample[feat] = value

            sample["label"] = class_name
            rows.append(sample)

    df = pd.DataFrame(rows)

    # Clamp ratio features to [0, 1]
    ratio_features = ["chlorosis_ratio", "decay_ratio", "tip_burn_ratio",
                       "pest_density", "wilting_ratio"]
    for feat in ratio_features:
        df[feat] = df[feat].clip(lower=0.0, upper=1.0)

    # Clamp VPD to >= 0
    df["instant_vpd"] = df["instant_vpd"].clip(lower=0.0)

    # Clamp cyclical features to [-1, 1]
    df["time_of_day_x"] = df["time_of_day_x"].clip(lower=-1.0, upper=1.0)
    df["time_of_day_y"] = df["time_of_day_y"].clip(lower=-1.0, upper=1.0)

    print(f"Generated {len(df)} samples across {len(CLASS_PROFILES)} classes.")
    return df


def train_model(df: pd.DataFrame) -> tuple:
    """
    Train an XGBClassifier on the synthetic data.

    Args:
        df: DataFrame with feature columns + 'label' column.

    Returns:
        Tuple of (model, label_encoder, feature_names, metrics_str).
    """
    # Encode labels
    le = LabelEncoder()
    y = le.fit_transform(df["label"])
    X = df[FEATURE_NAMES].values

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SPLIT, random_state=RANDOM_SEED, stratify=y
    )

    print(f"Training set: {len(X_train)} | Test set: {len(X_test)}")

    # Train
    clf = XGBClassifier(
        num_class=len(le.classes_),
        **XGB_PARAMS
    )
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    matrix = confusion_matrix(y_test, y_pred)

    print("\n--- Classification Report ---")
    print(report)
    print("--- Confusion Matrix ---")
    print(matrix)

    return clf, le, FEATURE_NAMES, report


def save_model(model, encoder, feature_names, path: Path):
    """
    Save the trained model bundle as a pickle file.

    The bundle contains:
        - "model": The trained XGBClassifier
        - "encoder": The LabelEncoder for class mapping
        - "features": Ordered list of feature names

    Args:
        model: Trained XGBClassifier.
        encoder: Fitted LabelEncoder.
        feature_names: List of feature name strings.
        path: Output file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    bundle = {
        "model": model,
        "encoder": encoder,
        "features": feature_names,
    }

    with open(path, "wb") as f:
        pickle.dump(bundle, f)

    size_kb = path.stat().st_size / 1024
    print(f"\nModel saved to: {path}")
    print(f"File size: {size_kb:.1f} KB")


if __name__ == "__main__":
    print("=" * 50)
    print("AeroSense Health Model Training")
    print("=" * 50)

    df = generate_synthetic_data()
    model, encoder, features, report = train_model(df)
    save_model(model, encoder, features, OUTPUT_PATH)

    print("\nDone. Copy models/health_model.pkl to the Pi to deploy.")
