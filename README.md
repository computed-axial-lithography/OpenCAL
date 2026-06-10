# OpenCAL — Open-Source Computed Axial Lithography Software

OpenCAL is open-source software for building and operating a **Computed Axial Lithography (CAL)** 3D printer — a volumetric, layer-less resin printing technique. It is designed to run headless on a Raspberry Pi 5 and is controlled through a hardware LCD/encoder interface.

> **This project is in active development.** Feedback and contributions are very welcome.

**Links:**
- [OpenCAL Documentation](https://opencal-org.readthedocs.io)
- [VAMToolbox Documentation](https://vamtoolbox.readthedocs.io) — for generating CAL-compatible print files
- [Discord Server](https://discord.com/invite/patduYdnSN)

---

## Table of Contents

1. [Overview](#overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Quick Start — Flashing the Pre-Built Image](#quick-start--flashing-the-pre-built-image)
4. [Building from Source](#building-from-source)
5. [Configuration](#configuration)
6. [Running as a systemd service](#running-as-a-systemd-service)
7. [Usage](#usage)
8. [Video File Naming Convention](#video-file-naming-convention)
9. [Contributing](#contributing)

---

## Overview

OpenCAL runs on a Raspberry Pi 5 and orchestrates all hardware needed for a CAL print job. All parameters are tunable via `opencal/utils/config.json`.

**Key components:**

- **LCD GUI** (`gui/lcd_gui.py`) — a state-machine menu controller for a 20×4 I2C LCD display. Drives all user interaction via a rotary encoder: file selection, settings, manual motor/LED control, alignment, and print start/stop.
- **Pygame GUI** (`gui/pygame_app.py`) — manages the projector display for precise interactive visuals during calibration and printing.
- **Print Controller** (`hardware/print_controller.py`) — orchestrates a full print job: spins up the stepper motor, activates LEDs, plays the video via `mpv`, and records via the camera.
- **Hardware Controller** (`hardware/hardware_controller.py`) — initializes all hardware at startup; failures are caught individually so the system continues in degraded mode rather than crashing.
- **Stepper Controller** (`hardware/stepper/tic_usb.py`) — controls the Pololu Tic T249 stepper motor controller over USB.
- **Projector Controller** (`hardware/projector_controller.py`) — `mpv`-based video playback with crop/zoom calibration for the print resin vial.
- **Camera Controller** (`hardware/camera_controller.py`) — `picamera2`-based capture and H264 video recording.
- **`config.json`** (`opencal/utils/config.json`) — single source of truth for all GPIO pins, I2C addresses, LED counts, camera type, default RPM, and projector calibration values.
- **`tic_settings.yaml`** (`opencal/utils/tic_settings.yaml`) — Pololu Tic T249 motor controller settings (current limit, step mode, acceleration) applied automatically on every startup.

**GUI features:**
1. Print from USB — automatically reads RPM from filename if present (see [naming convention](#video-file-naming-convention))
2. Manual Control — LEDs, stepper motor, image capture to USB
3. Settings — alignment tool, vial width finder, calibration images, USB video save prompt
4. Power Options — restart, power off, kill GUI
5. About — credits

---

## Hardware Requirements

| Component | Specification |
|---|---|
| **Computer** | Raspberry Pi 5 (2GB+ RAM) |
| **Storage** | microSD card ≥ 12GB |
| **Motor Controller** | Pololu Tic T249 (USB connection) |
| **Stepper Motor** | NEMA 17 (tested with 17HE19-2004S, 2.0A rated) |
| **LED Array** | 8×8 SK6812 RGBW NeoPixel matrix (64 LEDs) |
| **Display** | 20×4 I2C LCD (PCF8574 backpack, address 0x27) |
| **Encoder** | Rotary encoder with push button (GPIO 5, 6, 19) |
| **Camera** | Raspberry Pi Camera Module 3 (IMX708) |
| **Projector** | Any HDMI projector (tested with NexiGo Nova Mini) |

**Dependencies (installed automatically on the pre-built image):**
- Pololu `ticcmd` — command-line tool for the Tic motor controller
- `pi5neo` — NeoPixel/SK6812 control via SPI
- `picamera2` / `libcamera` — Raspberry Pi camera stack
- `mpv` — video playback for the projector
- `udiskie` — USB drive automounting

---

## Quick Start — Flashing the Pre-Built Image

The easiest way to get started is to flash the pre-built Raspberry Pi 5 image directly to a microSD card.

**Download:** [opencal_pi5.img.gz on Google Drive](https://drive.google.com/file/d/1HBJ7cH8QSTCckkTwJ3i0WToUSsLiP4YX/view?usp=sharing)

**Steps:**

1. Download `opencal_pi5.img.gz` from the link above
2. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
3. Open Raspberry Pi Imager
4. Click **"Choose OS"** → **"Use custom"** → select `opencal_pi5.img.gz`
5. Click **"Choose Storage"** → select your microSD card (≥ 12GB)
6. Click **"Write"** and wait for it to complete
7. Insert the SD card into your Raspberry Pi 5 and power on

The system will boot directly into OpenCAL. Default login credentials:
- **Username:** `opencal`
- **Password:** Set on first login (you will be prompted to change it)

> **Note:** The pre-built image already has the systemd service enabled and all hardware configured — you do not need to run any additional setup commands. The only things intentionally cleared from the image for security are WiFi credentials and SSH host keys (regenerated automatically on first boot).

**WiFi setup:** Place a `wifi.txt` file in the boot partition with the contents:
```
SSID=YourNetworkName
PASS=YourPassword
```

---

## Building from Source

**Prerequisites:** Raspberry Pi 5 running Raspberry Pi OS Bookworm

```bash
# Clone the repo
git clone https://github.com/computed-axial-lithography/OpenCAL.git
cd OpenCAL

# Install Python dependencies
pip install -r requirements.txt --break-system-packages

# Install Pololu Tic software (ticcmd)
# Download the ARM64 package from https://www.pololu.com/docs/0J71/3.2
# and install it with: sudo dpkg -i pololu-tic-*.deb

# Install udiskie for USB automounting
sudo apt install udiskie
```

Enable the user systemd service to start on boot:

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/opencal.path << 'EOF'
[Unit]
Description=Start OpenCAL when Wayland compositor is ready
[Path]
PathExists=%t/wayland-0
[Install]
WantedBy=default.target
EOF

cat > ~/.config/systemd/user/opencal.service << 'EOF'
[Unit]
Description=OpenCAL Printer Controller
[Service]
Type=simple
WorkingDirectory=/home/opencal/OpenCAL
ExecStart=/usr/bin/python3 -m opencal
Environment=SDL_VIDEODRIVER=wayland
Environment=WAYLAND_DISPLAY=wayland-0
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=DISPLAY=:0
StandardOutput=journal
StandardError=journal
Restart=on-failure
RestartSec=5
TimeoutStopSec=10
EOF

systemctl --user enable opencal.path
systemctl --user start opencal.path
loginctl enable-linger opencal
```

---

## Configuration

Edit `opencal/utils/config.json` to match your hardware:

```json
{
  "stepper_motor": {
    "driver_mode": "tic_usb",
    "A_pin": 12,
    "B_pin": 13,
    "default_rpm": 9,
    "default_direction": "CW",
    "steps_per_revolution": 3200
  },
  "rotary_encoder": {
    "clk_pin": 5,
    "dt_pin": 6,
    "btn_pin": 19
  }
}
```

**Motor controller settings** are stored in `opencal/utils/tic_settings.yaml` and are automatically written to the Tic on every startup — no manual configuration of the Tic is needed.

---

## Running as a systemd service

OpenCAL uses a **user-level systemd path unit** that watches for the Wayland display socket and starts the app automatically. See the setup commands in [Building from Source](#building-from-source) above.

To check status or view logs:

```bash
systemctl --user status opencal.service
journalctl --user -u opencal.service -f
```

To temporarily stop the app (e.g. for development):

```bash
systemctl --user disable opencal.path
systemctl --user kill -s SIGKILL opencal.service
```

Re-enable with:

```bash
systemctl --user enable opencal.path
```

---

## Usage

### Printing

1. Name your `.mp4` video file using the convention below and place it on a USB drive
2. Insert the USB drive into the Raspberry Pi
3. Navigate to **"Print from USB"** on the LCD menu
4. Select your file — the RPM is set automatically from the filename
5. Confirm or adjust the RPM, then confirm to start the print
6. When the print completes, click the encoder to stop — you will be prompted to save the recording to USB

### Calibration

Navigate to **Settings → Show Alignment** to display the cross-strut alignment tool image on the projector. Rotate the encoder to shift the image transversely for alignment.

Navigate to **Settings → Find Vial Width** to interactively size the projection to match your resin vial diameter.

### Capture Image

In **Manual Control → Capture image**, an image is captured and saved to USB (if connected) with a timestamp filename.

---

## Video File Naming Convention

OpenCAL reads the RPM value directly from the video filename. Name your files as:

```
<part_name>_<rpm>rpm.mp4
```

**Examples:**
- `cylinder_9rpm.mp4` → motor set to 9 RPM automatically
- `part_v2_12rpm.mp4` → motor set to 12 RPM automatically

If no RPM is found in the filename, the menu opens with the last-used RPM value.

---

## Contributing

Contributions are very welcome! Whether it's opening issues, reporting bugs, or submitting pull requests — all of it helps.

**Guidelines:**
- Keep code modularized and flexible via configuration (`config.json`) rather than hardcoded values.
- Follow the existing module structure — hardware drivers live in `hardware/`, GUI logic in `gui/`, utilities in `utils/`.
- If you are unsure about a change or want to discuss a feature before building it, reach out on the [Discord server](https://discord.com/invite/patduYdnSN).

**Automated image builds** are triggered by pushing a version tag of the form `v...` (e.g. `v1.0.0`). This kicks off the GitHub Actions workflow that produces a bootable Raspberry Pi 5 SD card image.
