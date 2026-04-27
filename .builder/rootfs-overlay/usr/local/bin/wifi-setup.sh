#!/bin/bash
# Reads SSID/PASSWORD from /boot/firmware/wifi.txt, creates a persistent
# NetworkManager connection profile, then deletes the file so the plaintext
# password does not remain on the boot partition.
# Always exits 0 — a bad password or unreachable AP is non-fatal.
set -uo pipefail

CONFIG="/boot/firmware/wifi.txt"

SSID=$(grep -m1 '^SSID=' "$CONFIG" | cut -d= -f2-)
PASSWORD=$(grep -m1 '^PASSWORD=' "$CONFIG" | cut -d= -f2-)

if [[ -z "$SSID" ]]; then
    echo "wifi-setup: SSID is empty in $CONFIG, skipping." >&2
    rm -f "$CONFIG"
    exit 0
fi

# Create a persistent autoconnect profile. If the AP is out of range or the
# password is wrong, NM saves the profile and retries automatically — the
# || true ensures a failed connection attempt does not fail the service.
nmcli connection add \
    type wifi \
    con-name "$SSID" \
    ssid "$SSID" \
    wifi-sec.key-mgmt wpa-psk \
    wifi-sec.psk "$PASSWORD" \
    connection.autoconnect yes || true

rm -f "$CONFIG"
echo "wifi-setup: profile created for '$SSID'."
