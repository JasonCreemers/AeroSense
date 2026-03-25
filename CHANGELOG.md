# Changelog
All notable changes to the **AeroSense** project will be documented in this file.

## [v5.2.0] - 2026-03-25
### Changed
- Switched MOSS model from llama3.1:8b to llama3.2:3b for faster CPU inference on Pi 5.

## [v5.1.0] - 2026-03-25
### Changed
- Switched MOSS model from gemma3:4b to llama3.1:8b for native tool calling support.

## [v5.0.0] - 2026-03-25
### Added
- Implemented MOSS with full CLI and GUI features.
- 11 MOSS tools including read sensors, run vision/health pipelines, play music, read files/logs, get system status, set mood.
- MOSS personality files including system prompt, plant care guidelines, fun facts, team profiles, jukebox guide.
- MOSS conversation management with auto-save, resume on reboot, 40-message sliding window, 30-day archive cleanup.
- MOSS stats tracking for total messages, tool calls, resets, first boot, last active.

## [v4.4.2] - 2026-03-24
### Changed
- Modified water log.

## [v4.4.1] - 2026-03-24
### Fixed
- Fixed `.gitignore`.

## [v4.4.0] - 2026-03-24
### Changed
- Upgraded system from Raspberry Pi 4B to Raspberry Pi 5 (16GB).

## [v4.3.9] - 2026-03-24
### Changed
- Restyled Audio category headers.

## [v4.3.8] - 2026-03-24
### Fixed
- Moved startup GRANTED sound earlier.
- Suppressed sensor interval log when no sensor cycles are active.
- Fixed random category button width in GUI.

## [v4.3.7] - 2026-03-24
### Fixed
- Restored startup GRANTED sound.
- Fixed random category button width in GUI.

## [v4.3.6] - 2026-03-24
### Added
- Added random category to CLI.

### Fixed
- Fixed PING SYSTEM always returning TIMEOUT.
- Removed startup GRANTED sound.

### Changed
- Modified Audio shuffle buttons in GUI.

## [v4.3.5] - 2026-03-24
### Added
- Added category shuffle buttons to Audio GUI panel.
- Added formatted startup output block.

### Fixed
- Fixed PING PONG storage.

### Changed
- Centered Plant Health feature values in GUI.

## [v4.3.4] - 2026-03-24
### Changed
- Modified masking borders.

## [v4.3.3] - 2026-03-24
### Changed
- Enabled borders around masking.
- Modified masking colors.

## [v4.3.2] - 2026-03-24
### Changed
- Moved Vision and Plant Health output into controller for GUI terminal parity.

## [v4.3.1] - 2026-03-24
### Added
- Added prediction confidence percentage to CLI and GUI output.
- Added feature values display to Plant Health GUI panel.
- Added Python version to `requirements.txt`.
- Added `.env` and `.md` files to `README.md`.

### Changed
- Renamed MOSS GUI panel to Plant Health.
- Changed necrosis overlay.

### Fixed
- Fixed duplicate GRANTED sound.

## [v4.3.0] - 2026-03-24
### Added
- Implemented XGBoost plant health classification system.
- Added `aerosense/ml/health.py` with 16-features.
- Added `RUN PLANT HEALTH` command.
- Added Plant Health panel to GUI.
- Added `health_log.csv`.
- Added `models/health_model.pkl` with 7 classes.

## [v4.2.1] - 2026-03-23
### Changed
- Upgraded to next Vision model.

## [v4.2.0] - 2026-03-23
### Changed
- Modified vision command.

## [v4.1.2] - 2026-03-23
### Fixed
- Fixed mismatched GUI coloring.

## [v4.1.1] - 2026-03-23
### Changed
- Modified Vision panel on GUI.

## [v4.1.0] - 2026-03-23
### Changed
- Switched vision inference from local model to RoboFlow cloud API.

## [v4.0.0] - 2026-03-23
### Added
- Implemented computer vision analysis system.
- Added RoboFlow instance segmentation integration.
- Added OpenCV green pixel counting for canopy analysis.
- Added Vision panel to GUI with annotated tile display.
- Added RUN VISION command to CLI and web interface.
- Added vision_log.csv for analysis data logging.
- Added .env support for secure API key management.

## [v3.16.10] - 2026-03-22
### Fixed
- Fixed Python importing discrepancy.

## [v3.16.9] - 2026-03-22
### Changed
- Modified tiling structure.

## [v3.16.8] - 2026-03-22
### Added
- Added new sad song.

## [v3.16.7] - 2026-03-22
### Changed
- Modified GUI camera code.

## [v3.16.6] - 2026-03-22
### Changed
- Modified GUI camera code.

## [v3.16.5] - 2026-03-22
### Changed
- Modified camera settings.

## [v3.16.4] - 2026-03-22
### Changed
- Modified camera settings.

## [v3.16.3] - 2026-03-22
### Changed
- Modified camera settings.

## [v3.16.2] - 2026-03-22
### Changed
- Modified camera settings.

## [v3.16.1] - 2026-03-22
### Changed
- General cleaning of the GUI UI.

## [v3.16.0] - 2026-03-21
### Added
- Implemented new splitting command to tile images for training data.

## [v3.15.3] - 2026-03-21
### Changed
- Modified GUI layout.

## [v3.15.2] - 2026-03-21
### Fixed
- Fixed broken songs.

## [v3.15.1] - 2026-03-21
### Added
- Modified Interstellar theme.
- Added sad SpongeBob theme.
- Added Succession theme.

## [v3.15.0] - 2026-03-20
### Fixed
- Fixed GUI page refresh on button press clearing terminal messages.
- Made sensor readings, timestamps, and ping statuses update live.
- Made camera image update automatically.
- Made cycle toggle buttons reflect state.

## [v3.14.0] - 2026-03-20
### Added
- Implemented two-way watchdog between Pi and Arduino.
- Added Pi heartbeat monitoring to firmware.
- Added automatic Arduino health check from Python.
- Added firmware safety cutoff for lights.

## [v3.13.0] - 2026-03-20
### Changed
- Upgraded environment and distance sensor filtering.
- Increased distance sensor buffer from 10 to 15 samples.
- Added validation for environment sensor.
- Added range validation for both sensors.
- Added staleness detection.

## [v3.12.0] - 2026-03-20
### Fixed
- Fixed duplicate pump safety monitor call in firmware.
- Fixed duplicate error sounds on sensor timeouts.
- Added stream buffer overflow protection for camera.
- Added reentry guard for WebSocket output capture.

## [v3.11.2] - 2026-03-20
### Fixed
- Fixed scheduling conflict for timed lights outside of active hours.

## [v3.11.1] - 2026-03-20
### Fixed
- Fixed lighting issue outside of active hours.

## [v3.11.0] - 2026-03-20
### Added
- Added MJPEG live camera streaming to Flask GUI.
- Added real-time terminal to GUI via WebSockets.

### Changed
- Major overhaul of GUI to support WebSockets.
- Modified camera logic to pause live stream during captures and resume after.

## [v3.10.2] - 2026-03-20
### Added
- Added armageddon countdown.

## [v3.10.1] - 2026-03-20
### Added
- Added Lights safety cutoff.
- Added lights runtime monitoring.
- Added lights state tracking .
- Added startup safety clear.
- Added ACK storage to support command verification.

## [v3.10.0] - 2026-03-20
### Fixed
- Fixed undefined song playback commands.
- Fixed camera subprocess timeout from 4000s to 10s.
- Added exception handling for camera capture sequence.

## [v3.9.1] - 2026-02-18
### Changed
- Modified `README.md`.

## [v3.9.0] - 2026-02-18
### Changed
- Modified system initialization and `README.md`.

## [v3.8.7] - 2026-01-29
### Fixed
- Fixed GitHub repository.

## [v3.8.6] - 2026-01-29
### Fixed
- Fixed GitHub repository.

## [v3.8.5] - 2026-01-29
### Fixed
- Fixed GitHub repository.

## [v3.8.4] - 2026-01-21
### Changed
- Removed test code for real.

## [v3.8.3] - 2026-01-21
### Changed
- Removed test code.
- Modified pump warning timing.

## [v3.8.2] - 2026-01-21
### Fixed
- Resolved versioning conflicts.

## [v3.8.1] - 2026-01-21
### Fixed
- Resolved scheduling collision between morning music inside active hours.

## [v3.8.0] - 2026-01-21
### Added
- Implemented smart warning tones for pump cycles.

### Changed
- Modified water pump cycle.
- Replaced `STATUS` button with `SYNC` in GUI diagnostics.
- Adjusted pump delay logic to accommodate longer warning songs.
- Added test code.

### Fixed
- Resolved scheduling collision between morning/night music and pump warnings.

## [v3.7.0] - 2026-01-18
### Added
- Expanded system health monitoring to `PI HEALTH` command.

### Changed
- Modified water pump cycle.
- Organized music library into categories and updated shuffle logic.

## [v3.6.0] - 2026-01-14
### Added
- Added audio safety warning before automated pump cycles.

### Changed
- Removed `SYNC` button from diagnostics panel in GUI.
- Migrated random song selection to Python controller.

### Fixed
- Fixed GUI camera button to handle capture delays.

## [v3.5.4] - 2026-01-14
### Changed
- Modified water level distance.

## [v3.5.3] - 2026-01-13
### Changed
- Modified camera settings to improve image quality.

## [v3.5.2] - 2026-01-13
### Changed
- Modified camera settings to improve image quality.

## [v3.5.1] - 2026-01-13
### Changed
- Modified water level distance.

## [v3.5.0] - 2026-01-13
### Changed
- Finalized physical implementation.

## [v3.4.3] - 2026-01-12
### Added
- Implemented centralized song validaion logic

### Changed
- Eliminated redundant audio feedback triggers during initialization.
- Replaced manual text input with interactive buttons for audio control on GUI.

### Fixed
- Refactored the live camera to a non-blocking background thread.
- Resolved concurreny issue with Arduino driver in `arduino.py`.
- Corrected formatting logic for version display

## [v3.4.2] - 2026-01-11
### Fixed 
- Fixed immediate hardware shutdown for pumps and lights when cycles are disabled.
- Resolved an issue where the GUI displayed outdated versioning.

## [v3.4.1] - 2026-01-11
### Fixed
- Resolved issue where `GUI` caused the CLI to hang.

## [v3.4.0] - 2026-01-11
### Added
- Implemented caching in `controller.py` to store most recent readings and pings.

### Changed
- Completely redesigned Flask GUI in `index.html` and `web.py`.

## [v3.3.0] - 2026-01-11
### Added
- Implemented `web.py` to drive a local Flask-based Graphical User Interface (GUI).
- Added `templates/index.html` to serve as the central dashboard for the GUI.

## [v3.2.0] - 2026-01-10
### Added
- Implemented a hardware Watchdog Timer (WDT) to protect against system lockups or hangs.
- Added split-brain protection incase Arduino reboots.
- Timeout length for camera.

### Changed
- Refactored `firmware.ino` to use C-style char[] arrays and strtak instead of String objects.
- Extended camera flash time pre-delay to 2s.
- Updated Pi Health to catch errors running on non-Linux platforms.

## [v3.1.0] - 2026-01-10
### Added
- `HARDWARE.md` to document pinouts and wiring schematics.
- `ROADMAP.md` for strategic project planning and task prioritization.
- `CHANGELOG.md` to standardize version history tracking.

### Changed
- Overhauled `README.md` to focus on system architecture and professional presentation.

## [v3.0.0] - 2026-01-10
### Changed
- **Major System Integration:** Finalized integration of hardware and software stacks.

## [v2.2.2] - 2026-01-09
### Added
- Audio feedback cues for system errors and positive confirmations.

### Changed
- Refactored birthday detection logic.

## [v2.2.1] - 2026-01-07
- Resolved persistent threading race condition in `controller.py`.

## [v2.2.0] - 2026-01-07
### Added
- Implemented timestamp validation in `arduino.py` to prevent the use of stale sensor data.

### Fixed
- Addressed ghost thread bottlenecks in `controller.py`.

## [v2.1.2] - 2026-01-07
### Added
- Added manual override status indicators to the `STATUS` command output.

## [v2.1.1] - 2026-01-07
### Added
- Introduced `RESET` command to clear manual overrides.

### Changed
- Updated morning music scheduling to trigger exclusively at 8:00 AM.
- Reduced console noise by cleaning up debug print statements.
- General code optimization.

## [v2.1.0] - 2026-01-07
### Added
- Initialized Version Control and GitHub integration.

### Changed
- Refactored `main.py` for better readability.

### Fixed
- Corrected lighting logic to ensure lights activate for camera captures outside of scheduled windows.
- Fixed synonym resolution for the `CYCLE` command.

## [v2.0.1] - 2026-01-06
### Added
- Expanded CLI vocabulary with new command synonyms.
- Added logging for automated light events triggered by the camera.
- Added result summaries to `RUN SENSORS` command output.
- Expanded music library and synchronized morning/evening playback with light cycles.

### Changed
- Standardized versioning and release variables.
- Updated `MUSIC PLAY NOTE` syntax to support duration arguments.
- Improved pump state tracking to gracefully handle manual shutoffs without triggering error states.

## [v2.0.0] - 2026-01-04
### Changed
- **Major Architecture Overhaul:** Transitioned to dual-controller design (Pi/Arduino).

## Legacy Versions
- **[v1.7.0]** - 2025-12-30
- **[v1.6.0]** - 2025-12-30
- **[v1.5.0]** - 2025-12-30
- **[v1.4.0]** - 2025-12-30
- **[v1.3.0]** - 2025-12-28
- **[v1.2.0]** - 2025-12-28
- **[v1.1.0]** - 2025-12-19
- **[v1.0.0]** - 2025-12-05