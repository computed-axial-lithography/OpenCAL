# OpenCAL Image — Getting Started

Flash the `.img.zst` file to a microSD card using [Raspberry Pi Imager](https://www.raspberrypi.com/software/) or `dd`. Insert into your Raspberry Pi 5 and power on.

---

## Default Login

| | |
|---|---|
| **Username** | `opencal` |
| **Password** | `OpenCAL1!` |

SSH is enabled by default. Connect over Ethernet and find the device IP via your router, or use `opencal.local` if mDNS is available on your network.

> **You will be required to change the password on your first SSH login.** Choose a strong password — the default credentials are public.

---

## WiFi Setup

WiFi credentials can be provided before first boot by editing the boot partition (the small FAT32 partition readable from any OS):

1. Copy `wifi.txt.example` → `wifi.txt` in the same directory on the boot partition
2. Fill in your network name and password:
   ```
   SSID=YourNetworkName
   PASSWORD=YourPassword
   ```
3. Eject the SD card and boot — credentials are applied automatically on first boot and `wifi.txt` is deleted so your password does not remain in plaintext

To configure WiFi after first boot, SSH in over Ethernet and run:
```bash
nmcli device wifi connect "YourNetworkName" password "YourPassword"
```

---

## OpenCAL Service

`opencal` starts automatically on boot as a systemd user service. It launches after the Wayland display compositor is ready.

Check service status over SSH:
```bash
systemctl --user status opencal
```

View live logs:
```bash
journalctl --user -u opencal -f
```

Restart the service:
```bash
systemctl --user restart opencal
```

---

## Display Configuration

The projector output resolution is detected automatically from the display's EDID. If your projector does not report EDID or you need to lock a specific resolution, edit `wayfire.ini` on the device:

```bash
nano /home/opencal/.config/wayfire/wayfire.ini
```

Add an output section with the desired resolution (use `wlr-randr` to list available modes):
```ini
[output:HDMI-A-1]
mode = 1920x1080@60
```
