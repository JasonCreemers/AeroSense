"""
AeroSense Package Initialization.

This module exposes the core components of the AeroSense system to the top-level package namespace, allowing for simplified imports. 
It also tracks the current versioning and release date.

Usage:
    >>> import aerosense
    >>> print(aerosense.__version__)
    >>> from aerosense import Controller
"""

from typing import List

# --- Versioning ---
__version__: str = "v3.8.0"
__release__: str = "2026-01-21"

# --- Component Exports ---
from .core.controller import Controller
from .core.logger import Logger
from .core.scheduler import Scheduler
from .hardware.arduino import Arduino
from .hardware.camera import Camera
from .interface.cli import CLI
from .interface.web import WebServer

# --- Public API ---
__all__: List[str] = [
    "Controller",
    "Logger",
    "Scheduler",
    "Arduino",
    "Camera",
    "CLI",
    "WebServer"
]