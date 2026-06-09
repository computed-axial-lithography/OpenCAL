# OpenCAL — Open-Source Computed Axial Lithography Software

OpenCAL is open-source software for building and operating a **Computed Axial Lithography (CAL)** 3D printer — a volumetric, layer-less resin printing technique. It is designed to run headless on a Raspberry Pi 5 and is controlled through a hardware LCD/encoder interface.

> **This project is in early stages of development.** Expect rough edges, breaking changes, and incomplete documentation. Feedback and contributions are very welcome.

**Links:**
- [OpenCAL Documentation](https://opencal-org.readthedocs.io)
- [VAMToolbox Documentation](https://vamtoolbox.readthedocs.io) — for generating CAL-compatible print files
- [Discord Server](https://discord.com/invite/patduYdnSN)

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Running as a systemd service](#running-as-a-systemd-service)
5. [Usage](#usage)
6. [Contributing](#contributing)

---

## Overview

OpenCAL runs on a Raspberry Pi 5 (no external monitor required after setup) and orchestrates all hardware needed for a CAL print job. All parameters are tunable via `opencal/utils/config.json`.

**Key components:**

- **LCD GUI** (`gui/lcd_gui.py`) — a state-machine menu controller for a 20×4 I2C LCD display. Drives all user interaction: file selection, settings editing, manual motor/LED control, and print start/stop.
- **Pygame GUI** (`gui/pygame_app.py`) — manages the projector display for precise interactive visuals during a print.
- **Print Controller** (`hardware/print_controller.py`) — orchestrates a full print job: spins up the stepper motor, activates LEDs, plays the video via `mpv`, and records via the camera.
- **Hardware Controller** (`hardware/hardware_controller.py`) — initializes all hardware at startup; failures are caught individually so the system continues in degraded mode rather than crashing.
- **Stepper Controller** (`hardware/stepper_controller.py`) — drives the GPIO stepper motor via `gpiozero`.
- **Projector Controller** (`hardware/projector_controller.py`) — `mpv`-based video playback with crop/zoom calibration for the print resin vial.
- **Camera Controller** (`hardware/camera_controller.py`) — `picamera2`-based capture and H264 video recording.
- **`config.json`** (`opencal/utils/config.json`) — single source of truth for all GPIO pins, I2C addresses, LED counts, camera type, default RPM, and projector calibration values.

**GUI features:**
1. Print from USB
2. Edit settings
3. Control stepper and LEDs manually
4. Scale the print size (%)
5. Kill GUI (useful when testing other functions on the Pi)

---

## Installation

Pre-built SD card images will be available for download (link TBD). These are the easiest way to get started on a Raspberry Pi 5.

Auto-generated images are also produced under the [Releases](../../releases) tab via GitHub Actions on every version tag — however, **this feature is still experimental** and images may not always be fully functional.

### Building from source

**Prerequisites:**

* System packages (listed in `apt_requirements.txt`)

**Steps:**

```bash
# Clone the repo
git clone https://github.com/computed-axial-lithography/OpenCAL.git
cd OpenCAL

# Install system dependencies
sudo apt update
xargs sudo apt install -y < apt_requirements.txt

# Create and activate virtual environment
python3 -m venv --use-system-packages
source .venv/bin/activate

# Install Python dependencies
python3 -m pip install -r requirements.txt
```

---

## Configuration

Edit `opencal/utils/config.json` to match your hardware setup. For example:

```json
{
  "rotary_encoder": {
    "clk_pin": 5,
    "dt_pin": 6,
    "btn_pin": 19
  }
}
```

---

## Running as a systemd service

To have OpenCAL start automatically at boot, register it as a `systemd` service:

1. **Copy the service file**

   ```bash
   sudo cp assets/opencal.service /etc/systemd/system/opencal.service
   ```

2. **Edit the service definition**

   ```bash
   sudo nano /etc/systemd/system/opencal.service
   ```

   Make sure to adjust the `User` and `WorkingDirectory` fields to match your installation. For example, if you cloned into `/home/opencal/OpenCAL` and created a `.venv` there, you might have:

   ```ini
   [Unit]
   Description=OpenCAL 3D Printer Service
   After=network.target

   [Service]
   User=opencal
   WorkingDirectory=/home/opencal/OpenCAL
   ExecStart=/home/opencal/OpenCAL/.venv/bin/python -m opencal
   Restart=on-failure
   ```

3. **Reload, enable, and start**

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable opencal.service
   sudo systemctl start opencal.service
   ```

4. **Verify it's running**

   ```bash
   sudo systemctl status opencal.service
   sudo journalctl -u opencal.service -f
   ```

* **`daemon-reload`** tells `systemd` to re-scan unit files.
* **`enable`** makes it start on every boot; **`start`** fires it now.
* **`status`** shows exit codes and recent logs; **`journalctl -f`** follows live output so you can spot errors immediately.

---

## Usage

If everything is properly connected and installed, the system can run entirely from the GUI. Expected sequence for printing:

1. Provide `.mp4` via USB storage device.
2. Navigate to "Print from USB" on the GUI.
3. Select `.mp4` file for printing.
4. Confirm the rotation speed (in rpm) of the resin (should be 9 for provided video).
5. Start the print or test.

---

## Contributing

Contributions are very welcome! Whether it's opening issues, reporting bugs, or submitting pull requests — all of it helps move the project forward.

**Guidelines:**
- Keep code modularized and flexible via configuration (`config.json`) rather than hardcoded values.
- Follow the existing module structure — hardware drivers live in `hardware/`, GUI logic in `gui/`, utilities in `utils/`.
- If you are unsure about a change or want to discuss a feature before building it, reach out on the [Discord server](https://discord.com/invite/patduYdnSN).

**Automated image builds** are triggered by pushing a version tag of the form `v...` (e.g. `v0.3.1`). This kicks off the GitHub Actions workflow that produces a bootable Raspberry Pi 5 SD card image and attaches it to the release. Note that automated builds are still experimental.
