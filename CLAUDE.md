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

**View opencal logs on a running image (user service):**
```bash
journalctl --user -u opencal.service -f
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
├── gui/
│   ├── lcd_gui.py  # LCDGui - state-machine menu controller for 20x4 LCD.
│   ├── pygame_app.py     # PygameApp - manages projector display for more precise interactive visuals.
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
- `PygameApp` and `LCDGui` commuincate via thread-safe queues to transfer focus and user inputs from hardware.

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

### Overview

A GitHub Actions workflow (`.github/workflows/build-image.yml`) triggers on version tags (`v*`) or manual dispatch. It uses [`rpi-image-gen`](https://github.com/raspberrypi/rpi-image-gen) to produce a bootable Raspberry Pi 5 SD card image, released as a compressed `.img.zst` file.

The workflow checks out both this repo and `rpi-image-gen`, copies `.builder/` into `rpi-image-gen/projects/OpenCAL/`, copies the OpenCAL source into `projects/OpenCAL/opencal-src/`, then runs `rpi-image-gen build`.

### Builder layout (`.builder/`)

```
.builder/
├── config.yaml                  # rpi-image-gen project config (device, image, layer settings)
├── layer/
│   └── opencal.yaml             # mmdebstrap layer: apt packages installed into the image
├── bdebstrap/
│   └── customize01.sh           # Post-install hook: copies source, enables hardware, builds venv
└── rootfs-overlay/              # Files copied verbatim into the image filesystem
    ├── etc/greetd/config.toml   # greetd autologin as opencal user, launches wayfire
    └── home/opencal/.config/
        ├── wayfire/wayfire.ini  # Wayfire compositor config (native Wayland, no Xwayland)
        └── systemd/user/
            ├── opencal.path     # Watches for Wayland socket; activates opencal.service
            └── opencal.service  # User service: runs `python -m opencal`
```

### Boot sequence

1. **greetd** autologs in as `opencal` and launches **wayfire** (native Wayland, no X11).
2. **libpam-systemd** (via PAM) registers the user session with logind, creating `/run/user/1000` and starting `systemd --user` for the `opencal` user.
3. **`opencal.path`** (user service) watches for `/run/user/1000/wayland-0` (the Wayland socket wayfire creates on startup).
4. Once the socket appears, systemd activates **`opencal.service`**, which runs `python -m opencal` with `SDL_VIDEODRIVER=wayland`.

### Key image details

- **Base**: Debian Bookworm minimal (`bookworm-minbase`) for RPi5
- **Display**: Native Wayland via wayfire — no Xwayland, no X11
- **Python**: venv at `/home/opencal/.venv` with `--system-site-packages` so apt-installed `python3-opencv` and `python3-picamera2` are visible
- **Hardware interfaces**: I2C and SPI enabled via `dtparam` entries in `config.txt` and `modules-load.d`
- **SSH**: Enabled with password auth; default credentials are `opencal` / `OpenCAL1!` — **the user is forced to change the password on first login** (`chage -d 0`)
- **Image size**: 512 MB boot partition + 4 GB root partition; does not auto-expand to fill the SD card

### Customise.sh responsibilities

`customize01.sh` runs inside the mmdebstrap chroot after all packages are installed. It:
1. Copies the OpenCAL source from `$SRCROOT/opencal-src` into `/home/opencal/OpenCAL`
2. Enables I2C and SPI via `config.txt` and `modules-load.d` (raspi-config cannot run in a build chroot)
3. Creates `/home/opencal/.venv`, pip-installs opencal + pygame + Pillow, then purges `build-essential`
4. Creates the user service enable symlink for `opencal.path`
5. Fixes ownership of `/home/opencal` in a single `chown -R`
6. Enables `greetd` via `systemctl enable`
7. Runs `chage -d 0 opencal` to force a password change on first login
