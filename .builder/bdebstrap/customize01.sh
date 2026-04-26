#!/bin/bash
set -euo pipefail

CHROOT="$1"

# 1. Copy OpenCAL source from SRCROOT (set by rpi-image-gen) into chroot
if [[ ! -d "$SRCROOT/opencal-src" ]]; then
    echo "ERROR: $SRCROOT/opencal-src not found." >&2
    echo "Ensure the workflow copies the OpenCAL source before building." >&2
    exit 1
fi
mkdir -p "$CHROOT/home/opencal/OpenCAL"
cp -r "$SRCROOT/opencal-src/." "$CHROOT/home/opencal/OpenCAL/"
chroot "$CHROOT" chown -R opencal:opencal /home/opencal/OpenCAL

# 2. Enable hardware interfaces and add user to hardware groups
chroot "$CHROOT" raspi-config nonint do_i2c 0
chroot "$CHROOT" raspi-config nonint do_spi 0
chroot "$CHROOT" usermod -aG i2c,spi,gpio,video,render opencal

# 3. Create venv with system-site-packages so apt-installed python3-opencv and
#    python3-picamera2 are visible, then install OpenCAL and undeclared runtime deps.
chroot "$CHROOT" sudo -u opencal python3 -m venv \
    --system-site-packages /home/opencal/.venv
chroot "$CHROOT" sudo -u opencal /home/opencal/.venv/bin/pip install --upgrade pip
chroot "$CHROOT" sudo -u opencal /home/opencal/.venv/bin/pip install \
    /home/opencal/OpenCAL pygame Pillow numpy

# 4. Enable greetd (Wayland autologin) and the opencal service.
#    Service and greetd config are already in the chroot via rootfs-overlay.
"$BDEBSTRAP_HOOKS/enable-units" "$CHROOT" greetd
"$BDEBSTRAP_HOOKS/enable-units" "$CHROOT" opencal

echo "OpenCAL customization complete."
