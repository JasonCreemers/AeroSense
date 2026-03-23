"""
AeroSense Vision Analyzer.

This module provides plant health analysis via computer vision.
It combines OpenCV-based green pixel counting with RoboFlow instance segmentation
to quantify canopy area and detect disease classes (chlorosis, necrosis, pest, tip_burn, wilting).
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from config import settings


# Vision overlay colors for each disease class
VISION_COLORS: Dict[str, Tuple[int, int, int]] = {
    "chlorosis": (0, 255, 255), # Yellow
    "necrosis": (42, 42, 165), # Brown
    "pest": (0, 0, 255), # Red
    "tip_burn": (0, 165, 255), # Orange
    "wilting": (255, 0, 128), # Purple
}


class VisionAnalyzer:
    """
    Performs plant health analysis on image tiles using OpenCV and RoboFlow.

    Attributes:
        log (logging.Logger): Dedicated logger for vision operations.
    """

    def __init__(self):
        """Initialize the VisionAnalyzer. Model loading is deferred to first use."""
        self.log = logging.getLogger("AeroSense.ML.Vision")
        self._model = None
        self._model_active: bool = False
        self._model_load_attempted: bool = False

    def _load_model(self) -> bool:
        """
        Lazy-load the RoboFlow inference model on first use.

        Returns:
            bool: True if model loaded successfully, False otherwise.
        """
        if self._model_load_attempted:
            return self._model_active

        self._model_load_attempted = True

        # Skip if no model ID configured
        if not settings.VISION_MODEL_ID:
            self.log.info("RoboFlow model not configured (VISION_MODEL_ID is empty).")
            return False

        try:
            from inference import get_model
            self._model = get_model(model_id=settings.VISION_MODEL_ID)
            self._model_active = True
            self.log.info("RoboFlow model loaded successfully.")
            return True

        except ImportError:
            self.log.warning("RoboFlow model not available: 'inference' package not installed.")
            return False

        except Exception as e:
            self.log.warning(f"RoboFlow model not available: {e}")
            return False

    def count_green_pixels(self, image_path: str) -> Tuple[int, int]:
        """
        Count green pixels in an image using HSV color space filtering.

        Args:
            image_path (str): Path to the image file.

        Returns:
            Tuple[int, int]: (total_pixels, green_pixels). Returns (0, 0) on failure.
        """
        try:
            import cv2
            import numpy as np

            img = cv2.imread(image_path)
            if img is None:
                self.log.error(f"Green count: Failed to read image: {image_path}")
                return (0, 0)

            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            lower = np.array(settings.VISION_GREEN_LOWER)
            upper = np.array(settings.VISION_GREEN_UPPER)
            mask = cv2.inRange(hsv, lower, upper)

            total_pixels = img.shape[0] * img.shape[1]
            green_pixels = int(cv2.countNonZero(mask))

            return (total_pixels, green_pixels)

        except Exception as e:
            self.log.error(f"Green count failed for {image_path}: {e}")
            return (0, 0)

    def run_inference_on_tile(self, image_path: str) -> Tuple[Dict[str, int], list]:
        """
        Run RoboFlow instance segmentation on a single tile.

        Args:
            image_path (str): Path to the tile image.

        Returns:
            Tuple[Dict[str, int], list]:
                - Dict mapping class names to pixel counts.
                - List of detection dicts with 'class_name' and 'points' for overlay drawing.
                Returns (all-zero dict, empty list) if model unavailable or on failure.
        """
        zero_counts = {cls: 0 for cls in settings.VISION_CLASSES}

        if not self._model_active or self._model is None:
            return (zero_counts, [])

        try:
            import cv2
            import numpy as np

            result = self._model.infer(image_path, confidence=settings.VISION_CONFIDENCE)

            # Handle result format
            if isinstance(result, list):
                result = result[0]

            predictions = result.predictions if hasattr(result, 'predictions') else []

            class_pixels: Dict[str, int] = {cls: 0 for cls in settings.VISION_CLASSES}
            detections: list = []

            img = cv2.imread(image_path)
            if img is None:
                return (zero_counts, [])

            height, width = img.shape[:2]

            for pred in predictions:
                class_name = pred.class_name.lower() if hasattr(pred, 'class_name') else ""

                if class_name not in settings.VISION_CLASSES:
                    continue

                # Extract segmentation polygon points
                if hasattr(pred, 'points'):
                    points = [(int(p.x), int(p.y)) for p in pred.points]
                else:
                    continue

                if len(points) < 3:
                    continue

                # Count pixels inside the polygon
                mask = np.zeros((height, width), dtype=np.uint8)
                pts = np.array([points], dtype=np.int32)
                cv2.fillPoly(mask, pts, 255)
                pixel_count = int(cv2.countNonZero(mask))

                class_pixels[class_name] += pixel_count
                detections.append({
                    "class_name": class_name,
                    "points": points
                })

            return (class_pixels, detections)

        except Exception as e:
            self.log.error(f"Inference failed for {image_path}: {e}")
            return (zero_counts, [])

    def draw_overlay(self, image_path: str, detections: list, output_path: str) -> bool:
        """
        Draw semi-transparent color overlays on a tile for each detection.

        Args:
            image_path (str): Path to the original tile image.
            detections (list): List of detection dicts with 'class_name' and 'points'.
            output_path (str): Path to save the annotated image.

        Returns:
            bool: True if saved successfully, False otherwise.
        """
        try:
            import cv2
            import numpy as np

            img = cv2.imread(image_path)
            if img is None:
                self.log.error(f"Overlay: Failed to read image: {image_path}")
                return False

            if not detections:
                return cv2.imwrite(output_path, img)

            overlay = img.copy()

            for det in detections:
                class_name = det["class_name"]
                points = det["points"]
                color = VISION_COLORS.get(class_name, (128, 128, 128))

                pts = np.array([points], dtype=np.int32)
                cv2.fillPoly(overlay, pts, color)

            # Blend at ~40% opacity
            result = cv2.addWeighted(overlay, 0.4, img, 0.6, 0)

            return cv2.imwrite(output_path, result)

        except Exception as e:
            self.log.error(f"Overlay failed for {image_path}: {e}")
            return False

    def analyze_all_tiles(self, tile_paths: List[str], vision_dir: Path, source_stem: str) -> Optional[Dict]:
        """
        Run the full vision pipeline across all 6 tiles.

        Args:
            tile_paths (List[str]): List of full paths to tile images.
            vision_dir (Path): Directory to save annotated vision tiles.
            source_stem (str): Stem of the original source image (for naming output files).

        Returns:
            Optional[Dict]: Aggregated results dict, or None if ALL tiles fail.
                Keys: total_pixels, green_pixels, class_pixels, vision_tiles, model_active
        """
        self._load_model()

        total_pixels = 0
        green_pixels = 0
        class_pixels: Dict[str, int] = {cls: 0 for cls in settings.VISION_CLASSES}
        vision_tiles: List[str] = []
        tiles_processed = 0

        for i, tile_path in enumerate(tile_paths, start=1):
            # Green pixel count
            t_total, t_green = self.count_green_pixels(tile_path)
            if t_total == 0:
                self.log.warning(f"Vision: Tile {i} unreadable, skipping.")
                continue

            total_pixels += t_total
            green_pixels += t_green
            tiles_processed += 1

            # RoboFlow inference
            t_class_pixels, detections = self.run_inference_on_tile(tile_path)
            for cls in settings.VISION_CLASSES:
                class_pixels[cls] += t_class_pixels.get(cls, 0)

            # Draw overlay and save
            vision_name = f"{source_stem}_{i}_vision.jpg"
            vision_path = str(vision_dir / vision_name)
            self.draw_overlay(tile_path, detections, vision_path)
            vision_tiles.append(vision_name)

        if tiles_processed == 0:
            self.log.error("Vision: All tiles failed to process.")
            return None

        self.log.info(f"Vision: Analyzed {tiles_processed}/{len(tile_paths)} tiles.")

        return {
            "total_pixels": total_pixels,
            "green_pixels": green_pixels,
            "class_pixels": class_pixels,
            "vision_tiles": vision_tiles,
            "model_active": self._model_active
        }
