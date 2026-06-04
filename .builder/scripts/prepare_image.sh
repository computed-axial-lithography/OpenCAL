#!/bin/bash
# prepare_image.sh — Clean sensitive data from a Pi image and shrink it.
#
# Usage:
#   sudo bash prepare_image.sh <path-to-image.img>
#
# What it removes:
#   - WiFi credentials
#   - SSH host keys (regenerated on first boot)
#   - SSH authorized keys
#   - Shell history for all users
#   - Machine ID (regenerated on first boot)
#   - Git credentials and config
#   - Raspberry Pi Connect credentials
#   - Crontab entries
#   - APT cache
#   - Log files
#   - Temp files
#   - Python/package caches
#
# Requires: losetup, pishrink.sh (downloaded automatically if not found)

set -euo pipefail

if [[ $EUID -ne 0 ]]; then
    echo "ERROR: Run this script with sudo." >&2
    exit 1
fi

if [[ -z "${1:-}" ]]; then
    echo "Usage: sudo bash prepare_image.sh <image.img>" >&2
    exit 1
fi

IMAGE="$1"

if [[ ! -f "$IMAGE" ]]; then
    echo "ERROR: Image file not found: $IMAGE" >&2
    exit 1
fi

echo "==> Attaching image: $IMAGE"
LOOP=$(losetup -fP --show "$IMAGE")
echo "    Using $LOOP"

ROOT_MOUNT=$(mktemp -d)
BOOT_MOUNT=$(mktemp -d)

cleanup() {
    echo "==> Cleaning up mounts..."
    umount "$ROOT_MOUNT" 2>/dev/null || true
    umount "$BOOT_MOUNT" 2>/dev/null || true
    rmdir "$ROOT_MOUNT" "$BOOT_MOUNT" 2>/dev/null || true
    losetup -d "$LOOP" 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Mounting partitions..."
mount "${LOOP}p2" "$ROOT_MOUNT"
mount "${LOOP}p1" "$BOOT_MOUNT"

echo "==> Removing WiFi credentials..."
rm -f "$ROOT_MOUNT/etc/NetworkManager/system-connections/"*.nmconnection

echo "==> Removing SSH host keys (will regenerate on first boot)..."
rm -f "$ROOT_MOUNT/etc/ssh/ssh_host_"*

echo "==> Removing SSH authorized keys..."
rm -f "$ROOT_MOUNT/home/opencal/.ssh/authorized_keys"
rm -f "$ROOT_MOUNT/root/.ssh/authorized_keys"

echo "==> Clearing shell history..."
rm -f "$ROOT_MOUNT/home/opencal/.bash_history"
rm -f "$ROOT_MOUNT/home/opencal/.zsh_history"
rm -f "$ROOT_MOUNT/root/.bash_history"
rm -f "$ROOT_MOUNT/root/.zsh_history"

echo "==> Resetting machine ID (will regenerate on first boot)..."
truncate -s 0 "$ROOT_MOUNT/etc/machine-id"
rm -f "$ROOT_MOUNT/var/lib/dbus/machine-id"

echo "==> Removing git credentials and personal config..."
rm -f "$ROOT_MOUNT/home/opencal/.git-credentials"
rm -f "$ROOT_MOUNT/home/opencal/.gitconfig"
rm -f "$ROOT_MOUNT/root/.git-credentials"
rm -f "$ROOT_MOUNT/root/.gitconfig"

echo "==> Removing Raspberry Pi Connect credentials..."
rm -rf "$ROOT_MOUNT/var/lib/rpi-connect/"*
rm -rf "$ROOT_MOUNT/home/opencal/.config/rpi-connect/"

echo "==> Clearing APT cache..."
rm -rf "$ROOT_MOUNT/var/cache/apt/archives/"*.deb
rm -rf "$ROOT_MOUNT/var/cache/apt/archives/partial/"*

echo "==> Clearing log files..."
find "$ROOT_MOUNT/var/log" -type f -exec truncate -s 0 {} \;

echo "==> Clearing temp files..."
rm -rf "$ROOT_MOUNT/tmp/"* "$ROOT_MOUNT/var/tmp/"*

echo "==> Clearing Python caches..."
find "$ROOT_MOUNT/home/opencal" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$ROOT_MOUNT/home/opencal" -name "*.pyc" -delete 2>/dev/null || true

echo "==> Unmounting..."
umount "$ROOT_MOUNT"
umount "$BOOT_MOUNT"
rmdir "$ROOT_MOUNT" "$BOOT_MOUNT"
losetup -d "$LOOP"
trap - EXIT

echo "==> Image cleaned."

# Run PiShrink if available, or download it
PISHRINK="$(dirname "$0")/pishrink.sh"
if [[ ! -f "$PISHRINK" ]]; then
    PISHRINK="./pishrink.sh"
fi
if [[ ! -f "$PISHRINK" ]]; then
    echo "==> Downloading PiShrink..."
    curl -fsSL https://raw.githubusercontent.com/Drewsif/PiShrink/master/pishrink.sh \
        -o "$PISHRINK"
    chmod +x "$PISHRINK"
fi

echo "==> Running PiShrink (shrink + gzip compress)..."
bash "$PISHRINK" -az "$IMAGE"

echo ""
echo "Done! Distributable image: ${IMAGE%.img}.img.gz"
echo "Flash with Raspberry Pi Imager on any Pi 5 with a >=12GB SD card."
