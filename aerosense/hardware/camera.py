"""
AeroSense Camera Driver.

This module provides a hardware driver for the Raspberry Pi Camera Module (IMX708).
It interfaces with the `rpicam-apps` (libcamera) suite to manage image capturing and live previews via the HDMI interface.
"""

import logging
import subprocess
from pathlib import Path
import time
from typing import List, Tuple

from config import settings

class Camera:
    """
    Hardware driver for the Raspberry Pi camera.

    Attributes:
        output_dir (Path): Directory where captured images are saved.
        resolution (Tuple[int, int]): Image dimensions (width, height).
        rotation (int): Image rotation in degrees (0, 90, 180, 270).
        vflip (bool): Vertical flip state.
        log (logging.Logger): Dedicated logger for camera operations.
    """

    def __init__(self):
        """
        Initialize the Camera driver with settings from the config module.
        """
        self.output_dir: Path = settings.IMG_DIR
        self.resolution: Tuple[int, int] = settings.CAM_RESOLUTION
        self.rotation: int = settings.CAM_ROTATION
        self.vflip: bool = settings.CAM_VFLIP
        
        self.log = logging.getLogger("AeroSense.Hardware.Camera")

    def capture_sequence(self, count: int) -> List[str]:
        """
        Capture a burst sequence of images.
        
        Args:
            count (int): The number of images to capture.

        Returns:
            List[str]: A list of generated filenames.
        """
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        generated_files = []
        
        self.log.info("Starting image capture sequence...")

        # Capture loop based on dynamic count
        for i in range(1, count + 1):
            filename = f"plant_{timestamp}_{i}.jpg"
            filepath = self.output_dir / filename
            
            # Build command arguments for rpicam-still
            cmd: List[str] = [
                "rpicam-still",
                "-o", str(filepath),
                "-t", "2000",
                "--width", str(self.resolution[0]),
                "--height", str(self.resolution[1]),
                "--nopreview"
            ]
            
            if self.rotation != 0:
                cmd.extend(["--rotation", str(self.rotation)])
                
            if self.vflip:
                cmd.append("--vflip")

            try:
                # Execute command
                subprocess.run(
                    cmd, 
                    check=True, 
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                generated_files.append(filename)
                
            except subprocess.CalledProcessError as e:
                # Handle execution errors
                error_msg = e.stderr.decode().strip() if e.stderr else "Unknown Error"
                self.log.error(f"Camera error on image {i}: {error_msg}")
                break
                
            except FileNotFoundError:
                # Handle missing system dependency
                self.log.critical("Command 'rpicam-still' not found. Ensure the camera library is installed.")
                break

            time.sleep(0.5)

        # Log summary
        if len(generated_files) == count:
            self.log.info(f"Sequence complete. Saved {len(generated_files)} images.")
        else:
            self.log.warning(f"Sequence incomplete. Saved {len(generated_files)}/{count} images.")

        return generated_files
    
    def start_preview(self, duration_sec: int):
        """
        Launch the live camera preview via the HDMI interface.

        Args:
            duration_sec (int): The duration in seconds to display the preview.
                                Pass 0 for an indefinite preview (until Ctrl+C).
        """
        if duration_sec == 0:
            self.log.info("Starting Live Preview (Indefinite)...")
        else:
            self.log.info(f"Starting Live Preview for {duration_sec}s...")
        
        # Build command arguments for rpicam-hello
        cmd = [
            "rpicam-hello",
            "-t", str(duration_sec * 1000),
            "--width", str(self.resolution[0]),
            "--height", str(self.resolution[1]),
        ]
        
        if self.rotation != 0:
            cmd.extend(["--rotation", str(self.rotation)])
        if self.vflip:
            cmd.append("--vflip")

        try:
            subprocess.run(cmd, check=True)
            self.log.info("Live Preview finished.")
            
        except subprocess.CalledProcessError:
            # Handle runtime errors
            self.log.error("Failed to launch preview. Ensure a monitor is attached.")
        except FileNotFoundError:
            # Handle missing system dependency
            self.log.critical("Command 'rpicam-hello' not found.")