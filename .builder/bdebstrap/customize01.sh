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
# Chown the entire home dir — the rootfs-overlay (wayfire.ini etc.) is copied
# as root, which leaves .config/ owned by root and causes shader-cache errors.
chroot "$CHROOT" chown -R opencal:opencal /home/opencal

# 2. Enable hardware interfaces and add user to hardware groups
# raspi-config cannot run in a build chroot (no configfs, no kernel modules),
# so directly edit config.txt and modules-load.d instead.
sed -i '/dtparam=i2c_arm/d;/dtparam=spi/d' "$CHROOT/boot/firmware/config.txt"
echo "dtparam=i2c_arm=on" >> "$CHROOT/boot/firmware/config.txt"
echo "dtparam=spi=on"     >> "$CHROOT/boot/firmware/config.txt"
echo "i2c-dev" >> "$CHROOT/etc/modules-load.d/raspi-extra.conf"
echo "spidev"  >> "$CHROOT/etc/modules-load.d/raspi-extra.conf"
chroot "$CHROOT" usermod -aG i2c,spi,gpio,video,render opencal

# 3. Create venv with system-site-packages so apt-installed python3-opencv and
#    python3-picamera2 are visible, then install OpenCAL and undeclared runtime deps.
# Run as root (sudo -u fails in a build chroot), then chown to opencal.
chroot "$CHROOT" python3 -m venv --system-site-packages /home/opencal/.venv
chroot "$CHROOT" /home/opencal/.venv/bin/pip install --upgrade pip
chroot "$CHROOT" /home/opencal/.venv/bin/pip install \
    /home/opencal/OpenCAL pygame Pillow
chroot "$CHROOT" chown -R opencal:opencal /home/opencal/.venv

# Wrapper so greetd can set up XDG_RUNTIME_DIR before launching wayfire.
# greetd itself does not create /run/user/<uid> — that requires libpam-systemd.
cat > "$CHROOT/usr/local/bin/start-wayfire" << 'EOF'
#!/bin/bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
mkdir -p "$XDG_RUNTIME_DIR"
chmod 0700 "$XDG_RUNTIME_DIR"
exec wayfire "$@"
EOF
chmod +x "$CHROOT/usr/local/bin/start-wayfire"

# 4. Enable greetd (Wayland autologin) and the opencal service.
#    Service and greetd config are already in the chroot via rootfs-overlay.
"$BDEBSTRAP_HOOKS/enable-units" "$CHROOT" greetd
"$BDEBSTRAP_HOOKS/enable-units" "$CHROOT" opencal

echo "OpenCAL customization complete."
