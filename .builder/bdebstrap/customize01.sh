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

# 2. Enable hardware interfaces.
# raspi-config cannot run in a build chroot (no configfs, no kernel modules),
# so directly edit config.txt and modules-load.d instead.
sed -i '/dtparam=i2c_arm/d;/dtparam=spi/d' "$CHROOT/boot/firmware/config.txt"
echo "dtparam=i2c_arm=on" >> "$CHROOT/boot/firmware/config.txt"
echo "dtparam=spi=on"     >> "$CHROOT/boot/firmware/config.txt"
echo "i2c-dev" >> "$CHROOT/etc/modules-load.d/raspi-extra.conf"
echo "spidev"  >> "$CHROOT/etc/modules-load.d/raspi-extra.conf"
chroot "$CHROOT" usermod -aG i2c,spi,gpio,video,render opencal

# Camera configuration.
# Disable auto-detection so it doesn't conflict with the manually specified overlay.
sed -i '/camera_auto_detect/d' "$CHROOT/boot/firmware/config.txt"
echo "camera_auto_detect=0" >> "$CHROOT/boot/firmware/config.txt"
# Camera overlay — edit this file on the boot partition (FAT32, readable from any OS)
# to change the camera. Common options are listed below.
cat >> "$CHROOT/boot/firmware/config.txt" << 'EOF'

# Camera overlay — uncomment the line matching your camera model, then reboot.
# The boot partition is FAT32 and can be edited from any computer.
dtoverlay=imx708             # Arducam / Raspberry Pi Camera Module 3 (default)
# dtoverlay=imx219           # Raspberry Pi Camera Module 2
# dtoverlay=imx477           # Raspberry Pi HQ Camera / Arducam IMX477
# dtoverlay=arducam-pivariety # Arducam 16MP / 64MP (needs Arducam driver)
EOF

# 3. Create venv with system-site-packages so apt-installed python3-opencv and
#    python3-picamera2 are visible, then install OpenCAL and remaining runtime deps.
#    Run as root (sudo -u fails in a build chroot); ownership is fixed in step 5.
chroot "$CHROOT" python3 -m venv --system-site-packages /home/opencal/.venv
chroot "$CHROOT" /home/opencal/.venv/bin/pip install --upgrade pip
chroot "$CHROOT" /home/opencal/.venv/bin/pip install \
    /home/opencal/OpenCAL pygame Pillow
# TODO: install opencv via pip once the build is stable. pip is used instead of
# the apt package because python3-opencv from Debian Bookworm is compiled against
# numpy 1.x, which conflicts with python3-picamera2 (RPi repo, numpy 2.x).
# pip's opencv-python-headless ships aarch64 wheels built against numpy 2.x.
# chroot "$CHROOT" /home/opencal/.venv/bin/pip install opencv-python-headless
# build-essential was only needed to compile the pip packages above; remove it
# from the final image to avoid shipping gcc/make on a production device.
chroot "$CHROOT" apt-get purge -y --autoremove build-essential

# 4. Enable the user service via a symlink (systemctl --user cannot run in a chroot).
#    opencal.path fires when the Wayland socket appears, then activates opencal.service.
mkdir -p "$CHROOT/home/opencal/.config/systemd/user/default.target.wants"
ln -sf /home/opencal/.config/systemd/user/opencal.path \
    "$CHROOT/home/opencal/.config/systemd/user/default.target.wants/opencal.path"

# 5. Fix ownership of the entire home directory in one pass.
#    This covers: the OpenCAL source, the rootfs-overlay files (.config/wayfire,
#    .config/systemd), and the venv — all of which were written as root above.
chroot "$CHROOT" chown -R opencal:opencal /home/opencal

# 6. Enable greetd for Wayland autologin.
"$BDEBSTRAP_HOOKS/enable-units" "$CHROOT" greetd

# 7. Force password change on first login so the default credentials don't persist.
chroot "$CHROOT" chage -d 0 opencal

echo "OpenCAL customization complete."
