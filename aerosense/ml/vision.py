"""
AeroSense Vision Analyzer.

This module provides plant health analysis via computer vision.
It combines OpenCV-based green pixel counting with RoboFlow instance segmentation
to quantify canopy area and detect disease classes (chlorosis, necrosis, pest, tip_burn, wilting).
"""

import base64
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

from config import settings


# Vision overlay colors for each disease class
VISION_COLORS: Dict[str, Tuple[int, int, int]] = {
    "chlorosis": (0, 255, 255), # Yellow
    "necrosis": (50, 50, 50), # Dark Gray
    "pest": (0, 0, 255), # Red
    "tip_burn": (0, 165, 255), # Orange
    "wilting": (255, 0, 128), # Purple
}

# RoboFlow API endpoint for instance segmentation
ROBOFLOW_API_URL = "https://outline.roboflow.com"


class VisionAnalyzer:
    """
    Performs plant health analysis on image tiles using OpenCV and RoboFlow.

    Attributes:
        log (logging.Logger): Dedicated logger for vision operations.
    """

    def __init__(self):
        """Initialize the VisionAnalyzer. API readiness is checked on first use."""
        self.log = logging.getLogger("AeroSense.ML.Vision")
        self._model_active: bool = False
        self._model_check_done: bool = False
        self._api_key: str = ""

    def _check_api(self) -> bool:
        """
        Check that the RoboFlow API key and model ID are configured.

        Returns:
            bool: True if API is ready, False otherwise.
        """
        if self._model_check_done:
            return self._model_active

        self._model_check_done = True

        if not settings.VISION_MODEL_ID:
            self.log.info("RoboFlow model not configured (VISION_MODEL_ID is empty).")
            return False

        self._api_key = os.getenv("ROBOFLOW_API_KEY", "")
        if not self._api_key:
            self.log.warning("RoboFlow API key not set in environment.")
            return False

        self._model_active = True
        self.log.info("RoboFlow API configured successfully.")
        return True

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
        Run RoboFlow instance segmentation on a single tile via HTTP API.

        Args:
            image_path (str): Path to the tile image.

        Returns:
            Tuple[Dict[str, int], list]:
                - Dict mapping class names to pixel counts.
                - List of detection dicts with 'class_name' and 'points' for overlay drawing.
                Returns (all-zero dict, empty list) if API unavailable or on failure.
        """
        zero_counts = {cls: 0 for cls in settings.VISION_CLASSES}

        if not self._model_active:
            return (zero_counts, [])

        try:
            import cv2
            import numpy as np

            # Encode image as base64
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            # Call RoboFlow API
            url = f"{ROBOFLOW_API_URL}/{settings.VISION_MODEL_ID}"
            resp = requests.post(
                url,
                params={
                    "api_key": self._api_key,
                    "confidence": int(settings.VISION_CONFIDENCE * 100),
                },
                data=img_b64,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30,
            )
            resp.raise_for_status()
            result = resp.json()

            predictions = result.get("predictions", [])

            class_pixels: Dict[str, int] = {cls: 0 for cls in settings.VISION_CLASSES}
            detections: list = []

            img = cv2.imread(image_path)
            if img is None:
                return (zero_counts, [])

            height, width = img.shape[:2]

            for pred in predictions:
                class_name = pred.get("class", "").lower()

                if class_name not in settings.VISION_CLASSES:
                    continue

                # Extract segmentation polygon points
                points_raw = pred.get("points", [])
                points = [(int(p["x"]), int(p["y"])) for p in points_raw]

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

        Saves individual annotated tiles to tiled_vision/, then stitches them
        into a single combined image saved to vision/.

        Args:
            tile_paths (List[str]): List of full paths to tile images.
            vision_dir (Path): Directory to save the combined vision image.
            source_stem (str): Stem of the original source image (for naming output files).

        Returns:
            Optional[Dict]: Aggregated results dict, or None if ALL tiles fail.
                Keys: total_pixels, green_pixels, class_pixels, vision_image, model_active
        """
        self._check_api()

        total_pixels = 0
        green_pixels = 0
        class_pixels: Dict[str, int] = {cls: 0 for cls in settings.VISION_CLASSES}
        tiled_paths: List[str] = []
        tiles_processed = 0

        tiled_dir = settings.TILED_VISION_DIR

        for i, tile_path in enumerate(tile_paths, start=1):
            # Green pixel count
            t_total, t_green = self.count_green_pixels(tile_path)
            if t_total == 0:
                self.log.warning(f"Vision: Tile {i} unreadable, skipping.")
                tiled_paths.append(tile_path)
                continue

            total_pixels += t_total
            green_pixels += t_green
            tiles_processed += 1

            # RoboFlow inference
            t_class_pixels, detections = self.run_inference_on_tile(tile_path)
            for cls in settings.VISION_CLASSES:
                class_pixels[cls] += t_class_pixels.get(cls, 0)

            # Draw overlay and save to tiled_vision/
            tiled_name = f"{source_stem}_{i}_tiled_vision.jpg"
            tiled_path = str(tiled_dir / tiled_name)
            if self.draw_overlay(tile_path, detections, tiled_path):
                tiled_paths.append(tiled_path)
            else:
                tiled_paths.append(tile_path)

        if tiles_processed == 0:
            self.log.error("Vision: All tiles failed to process.")
            return None

        # Stitch 6 tiles into one combined image (3 columns x 2 rows)
        vision_image = self._stitch_tiles(tiled_paths, vision_dir, source_stem)

        self.log.info(f"Vision: Analyzed {tiles_processed}/{len(tile_paths)} tiles.")

        return {
            "total_pixels": total_pixels,
            "green_pixels": green_pixels,
            "class_pixels": class_pixels,
            "vision_image": vision_image,
            "model_active": self._model_active
        }

    def _stitch_tiles(self, tile_paths: List[str], vision_dir: Path, source_stem: str) -> Optional[str]:
        """
        Combine 6 tile images into a single 3x2 grid image.

        Args:
            tile_paths (List[str]): List of 6 tile image paths.
            vision_dir (Path): Directory to save the combined image.
            source_stem (str): Stem name for the output file.

        Returns:
            Optional[str]: Filename of the combined image, or None on failure.
        """
        try:
            import cv2
            import numpy as np

            tiles = []
            for tp in tile_paths:
                img = cv2.imread(tp)
                if img is None:
                    self.log.error(f"Stitch: Failed to read tile: {tp}")
                    return None
                tiles.append(img)

            # Normalize tile sizes (last col/row may differ by 1-2px)
            tile_h = min(t.shape[0] for t in tiles)
            tile_w = min(t.shape[1] for t in tiles)
            tiles = [t[:tile_h, :tile_w] for t in tiles]

            # Build 2 rows of 3 tiles each
            row_top = np.hstack(tiles[0:3])
            row_bot = np.hstack(tiles[3:6])
            combined = np.vstack([row_top, row_bot])

            vision_name = f"{source_stem}_vision.jpg"
            vision_path = str(vision_dir / vision_name)
            cv2.imwrite(vision_path, combined)

            return vision_name

        except Exception as e:
            self.log.error(f"Stitch failed: {e}")
            return None
