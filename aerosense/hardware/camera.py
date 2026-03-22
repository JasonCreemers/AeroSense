"""
AeroSense Camera Driver.

This module provides a hardware driver for the Raspberry Pi Camera Module (IMX708).
It interfaces with the `rpicam-apps` (libcamera) suite to manage image capturing,
live HDMI previews, and MJPEG streaming for the web interface.
"""

import logging
import subprocess
import threading
from pathlib import Path
import time
from typing import List, Optional, Tuple

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
        is_streaming (bool): Whether the MJPEG stream is currently active.
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

        # MJPEG stream state
        self._stream_process: Optional[subprocess.Popen] = None
        self._stream_thread: Optional[threading.Thread] = None
        self._stream_lock = threading.Lock()
        self._frame_lock = threading.Lock()
        self._latest_frame: Optional[bytes] = None
        self.is_streaming: bool = False

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
                "-t", "5000",
                "--width", str(self.resolution[0]),
                "--height", str(self.resolution[1]),
                "--nopreview",
                '--autofocus-mode', 'auto',
                '--autofocus-on-capture',
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
                    timeout=10,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE
                )
                generated_files.append(filename)

            except subprocess.CalledProcessError as e:
                # Handle execution errors
                error_msg = e.stderr.decode().strip() if e.stderr else "Unknown Error"
                self.log.error(f"Camera error on image {i}: {error_msg}")
                break

            except subprocess.TimeoutExpired:
                # Handle hung camera process
                self.log.error(f"Camera timed out on image {i}. Aborting sequence.")
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
            calc_timeout = None if duration_sec == 0 else (duration_sec + 2)
            subprocess.run(cmd, check=True, timeout=calc_timeout)
            self.log.info("Live Preview finished.")
            
        except subprocess.CalledProcessError:
            # Handle runtime errors
            self.log.error("Failed to launch preview. Ensure a camera is attached.")
        except FileNotFoundError:
            # Handle missing system dependency
            self.log.critical("Command 'rpicam-still' not found. Ensure the camera library is installed.")

    # --- MJPEG Streaming ---
    def start_stream(self) -> bool:
        """
        Start an MJPEG stream from the camera via rpicam-vid.
        Frames are read in a background thread and stored for retrieval.

        Returns:
            bool: True if stream started successfully, False otherwise.
        """
        with self._stream_lock:
            if self.is_streaming:
                self.log.warning("Stream already active.")
                return True

            cmd = [
                "rpicam-vid",
                "--codec", "mjpeg",
                "--inline",
                "-t", "0",
                "--width", str(self.resolution[0]),
                "--height", str(self.resolution[1]),
                "--nopreview",
                "--framerate", "15",
                "-o", "-",
            ]

            if self.rotation != 0:
                cmd.extend(["--rotation", str(self.rotation)])
            if self.vflip:
                cmd.append("--vflip")

            try:
                self._stream_process = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
            except FileNotFoundError:
                self.log.critical("Command 'rpicam-vid' not found. Cannot start stream.")
                return False
            except Exception as e:
                self.log.error(f"Failed to start stream: {e}")
                return False

            self.is_streaming = True
            self._stream_thread = threading.Thread(target=self._read_frames, daemon=True)
            self._stream_thread.start()
            self.log.info("MJPEG stream started.")
            return True

    def stop_stream(self):
        """Stop the MJPEG stream and clean up the subprocess."""
        with self._stream_lock:
            if not self.is_streaming:
                return

            self.is_streaming = False

            if self._stream_process:
                try:
                    self._stream_process.terminate()
                    self._stream_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._stream_process.kill()
                    self._stream_process.wait(timeout=2)
                except Exception as e:
                    self.log.error(f"Error stopping stream process: {e}")
                self._stream_process = None

            with self._frame_lock:
                self._latest_frame = None

            self.log.info("MJPEG stream stopped.")

    def get_frame(self) -> Optional[bytes]:
        """
        Retrieve the most recent JPEG frame from the live stream.

        Returns:
            Optional[bytes]: Raw JPEG data, or None if no frame available.
        """
        with self._frame_lock:
            return self._latest_frame

    def _read_frames(self):
        """Background thread: reads MJPEG frames from rpicam-vid stdout."""
        buf = b''
        MAX_BUF = 1024 * 1024  # 1MB safety cap
        try:
            while self.is_streaming and self._stream_process:
                chunk = self._stream_process.stdout.read(4096)
                if not chunk:
                    break
                buf += chunk

                # Safety: discard buffer if it grows too large (corrupted stream)
                if len(buf) > MAX_BUF:
                    self.log.warning("Stream buffer overflow. Discarding corrupted data.")
                    buf = b''
                    continue

                # Extract complete JPEG frames (SOI: FFD8, EOI: FFD9)
                while True:
                    start = buf.find(b'\xff\xd8')
                    end = buf.find(b'\xff\xd9')
                    if start != -1 and end != -1 and end > start:
                        frame = buf[start:end + 2]
                        with self._frame_lock:
                            self._latest_frame = frame
                        buf = buf[end + 2:]
                    else:
                        break

        except Exception as e:
            self.log.error(f"Stream reader error: {e}")

        # Clean up if the process exited unexpectedly
        if self.is_streaming:
            self.log.warning("Stream process ended unexpectedly.")
            self.is_streaming = False