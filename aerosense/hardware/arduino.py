"""
AeroSense Arduino Driver.

This module handles low-level serial communication with the Arduino Mega 2560.
It implements a threaded listener pattern to ensure non-blocking I/O, allowing the system to receive hardware alerts instantly while the main thread is busy.
"""

import logging
import threading
import time
from typing import Dict, Optional

import serial

from config import settings

class Arduino:
    """
    Hardware driver for the Arduino Mega 2560.

    Attributes:
        port (str): The serial port (e.g., /dev/ttyACM0).
        baud (int): Baud rate for communication (must match firmware).
        data_store (Dict[str, str]): Thread-safe buffer for incoming sensor data.
        running (bool): Flag to control the background listener thread.
    """

    def __init__(self):
        """
        Initialize the driver and attempt immediate connection.
        """
        # Serial communication settings
        self.port: str = settings.SERIAL_PORT
        self.baud: int = settings.BAUD_RATE
        self.timeout: int = settings.SERIAL_TIMEOUT
        self.max_retries: int = settings.MAX_RETRIES
        
        self.ser: Optional[serial.Serial] = None
        self.log = logging.getLogger("AeroSense.Hardware.Arduino")

        # Threading primitives
        self.data_store: Dict[str, str] = {}
        self.data_lock = threading.Lock()
        self.serial_lock = threading.Lock()
        
        self.running: bool = False
        self.listener_thread: Optional[threading.Thread] = None
        self.reboot_detected = False
        
        # Attempt connection immediately
        if self.connect():
            self.start_listener()

    def connect(self) -> bool:
        """
        Establish the serial connection with retry logic.

        Returns:
            bool: True if connection successful, False otherwise.
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # Attempt serial connection and log attempt
                self.log.info(f"Connecting to Arduino on {self.port} (Attempt {attempt}/{self.max_retries})...")
                self.ser = serial.Serial(self.port, self.baud, timeout=self.timeout)
                time.sleep(2)
                self.ser.reset_input_buffer()
                self.log.info("Serial connection established.")
                return True
            except serial.SerialException as e:
                # Handle connection errors
                self.log.error(f"Connection failed: {e}")
                if attempt < self.max_retries:
                    time.sleep(1)
                else:
                    self.log.critical("Max retries reached. Arduino unavailable.")
        
        return False

    def disconnect(self):
        """
        Cleanly close the serial connection and stop the listener.
        """
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.log.info("Serial connection closed.")

    def start_listener(self):
        """
        Spin up the background thread to listen for incoming serial data.
        """
        self.running = True
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

    def _listen_loop(self):
        """
        Background loop that continuously reads from the serial port.
        It parses incoming lines and routes them based on their prefix:
        """
        while self.running and self.ser and self.ser.is_open:
            try:
                # Check if data is wating in hardware buffer
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if not line: continue

                    now = time.time()
                    
                    # --- Critical Alerts ---
                    if line.startswith("ALERT"):
                        self.log.critical(f"HARDWARE ALERT: {line}")
                    
                    # --- Command Ackowledgments ---
                    elif line.startswith("ACK"):
                        self.log.info(f"ARDUINO: {line}")
                        
                    # --- Sensor Data ---
                    elif line.startswith("DATA"):
                        if ":" in line:
                            tag, value = line.split(":", 1)
                            with self.data_lock:
                                self.data_store[tag] = (value, now)
                        
                    # --- Ping Response ---
                    elif line.startswith("PONG"):
                        value = "OK"
                        if ":" in line:
                            _, value = line.split(":", 1)
                            
                        with self.data_lock:
                            self.data_store["PONG"] = (value, now)

                    # --- System Reboot ---
                    elif line == "SYSTEM:READY":
                        self.log.warning("Arduino Reboot Detected! Triggering state sync.")
                        self.reboot_detected = True

            except Exception as e:
                # Catch unknown errors
                self.log.error(f"Listener Error: {e}")
                time.sleep(0.1)

    def send(self, command: str) -> bool:
        """
        Send a raw command string to the Arduino.
        Includes logic to automatically reconnect if the connection dropped.

        Args:
            command (str): The command string (e.g., "PUMP ON").

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        # Check connection status
        if not self.ser or not self.ser.is_open:
            # Attempt to reconnect if connection is lost
            self.log.warning("Connection lost. Attempting to reconnect...")
            
            if not self.connect():
                 # Disconnect from hardware
                 self.log.error("Reconnect failed. Command dropped.")
                 return False
            
            # Restart listener thread after reconnection
            self.start_listener() 
            self.log.info("Listener thread restarted.")

        try:
            # Append newline character

            full_cmd = f"{command}\n"
            with self.serial_lock:
                self.ser.write(full_cmd.encode('utf-8'))
            return True
            
        except serial.SerialTimeoutException:
            # Handle buffer errors
            self.log.error(f"Timeout sending command: {command}")
            return False
            
        except Exception as e:
            # Handle IO errors
            self.log.error(f"Serial write error: {e}")
            self.disconnect() 
            return False
        
    def get_latest_data(self, tag: str, min_timestamp: float, timeout: float = 0.5) -> Optional[str]:
        """
        Retrieve specific data from the internal buffer, ensuring it is fresh.
        
        This method waits up to `timeout` seconds for data to appear in the thread-safe `data_store` that has a timestamp newer than `min_timestamp`.

        Args:
            tag (str): The data prefix to search for (e.g., "DATA_TEMP").
            min_timestamp (float): The timestamp of the request. Data older than this is rejected.
            timeout (float): Max time to wait in seconds.

        Returns:
            Optional[str]: The value part of the message, or None if timed out.
        """
        start = time.time()
        while (time.time() - start) < timeout:
            with self.data_lock:
                if tag in self.data_store:
                    val, ts = self.data_store[tag]
                    
                    if ts > min_timestamp:
                        return val
                        
            time.sleep(0.05)
                
        return None
    
    def ping(self, timeout: float = 1.0) -> bool:
        """
        Send a PING command and wait for a PONG response.
        Used to verify the MCU is responsive and not hanging.

        Args:
            timeout (float): The maximum time (in seconds) to wait for response.

        Returns:
            bool: True if 'PONG' received, False otherwise.
        """
        start_time = time.time()
                
        # Send command
        if not self.send("PING"):
            return False
            
        # Wait for response and clear old data
        response = self.get_latest_data("PONG", min_timestamp=start_time, timeout=timeout)
        return response is not None