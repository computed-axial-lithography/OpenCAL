# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OpenCAL is an open-source Computed Axial Lithography (CAL) 3D printer software system designed to run headless on a Raspberry Pi 5. It controls hardware (stepper motor, LED array, projector via mpv, camera, LCD display, rotary encoder) through a menu-driven LCD interface.

## Commands

**Install system dependencies (Raspberry Pi only):**
```bash
sudo apt update && xargs sudo apt install -y < apt-requirements.txt
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Run the application:**
```bash
python -m opencal
```

**Run as systemd service:**
```bash
sudo systemctl start opencal.service
sudo journalctl -u opencal.service -f   # view logs
```

**Build docs:**
```bash
cd docs && make html
```

There are no automated tests — only manual hardware test scripts: `camera_test.py`, `make_calibration.py`, `vial_width.py`.

## Architecture

### Module Layout

```
opencal/
├── __main__.py               # Entry point: starts LCDGui in a daemon thread
├── gui/lcd_gui.py            # LCDGui — state-machine menu controller
├── hardware/
│   ├── hardware_controller.py  # Initializes all hardware; tracks degraded state
│   ├── print_controller.py     # Orchestrates a full print job (motor + LED + projector + camera)
│   ├── camera_controller.py    # picamera2 capture/video
│   ├── stepper_controller.py   # GPIO stepper via gpiozero
│   ├── projector_controller.py # mpv-based video playback with crop/zoom
│   ├── led_manager.py          # Pi5Neo addressable LED ring (64 LEDs)
│   ├── lcd_display.py          # RPLCD 20×4 I2C LCD (address 0x27)
│   ├── rotary_controller.py    # Rotary encoder input
│   └── usb_manager.py          # USB file discovery (.mp4 files)
└── utils/
    ├── config.py               # Typed config loaders (dataclasses)
    └── config.json             # All hardware pin/address/parameter values
```

### Key Relationships

- `LCDGui` owns a `PrintController` and drives all user interaction through a nested enum-based menu state machine.
- `PrintController` owns and orchestrates `HardwareController`, coordinating motor, LEDs, projector, and camera in a single print thread.
- `HardwareController` initializes every component at startup; failures are logged and the system continues in degraded mode rather than crashing.
- All GPIO pins, I2C addresses, LED counts, and print defaults are set in `opencal/utils/config.json` and loaded into typed dataclasses (`StepperConfig`, `CameraConfig`, `LedArrayConfig`, etc.).

### Print Job Flow

1. User selects a `.mp4` file from USB via the LCD menu.
2. `PrintController.start_print_job()` spawns a thread calling `PrintController.print()`.
3. The print thread: starts stepper (CCW), sets LEDs to red, plays video via `mpv` with a crop filter sized to the configured print percentage, begins camera recording to H264.
4. On stop: motor, LEDs, projector, and camera are cleaned up in order.

### Hardware Coupling

Most imports (`gpiozero`, `picamera2`, `pi5neo`, `lgpio`) only work on a Raspberry Pi 5. Development on non-RPi hardware requires mocking or skipping these imports. `HardwareController` wraps each init in try/except for this reason.

## Configuration

Edit `opencal/utils/config.json` to change GPIO pins, I2C address, LED count, camera type, default RPM, or projector calibration. The `Config` class in `utils/config.py` loads this file at startup into typed dataclasses that are passed to each hardware component.

## Deployment

A GitHub Actions workflow (`.github/workflows/build-image.yml`) triggers on version tags (`v*`) and uses `rpi-image-gen` to produce a bootable Raspberry Pi SD card image released as a compressed `.img.xz` file.
