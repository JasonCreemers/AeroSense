# Changelog
All notable changes to the **AeroSense** project will be documented in this file.

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