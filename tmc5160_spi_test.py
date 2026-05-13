#!/usr/bin/env python3
"""
tmc5160_spi_test.py — Standalone SPI test for BigTreeTech TMC5160 Pro on RPi5.
Usage: python3 tmc5160_spi_test.py
"""

# ============================================================
# WIRING (BCM GPIO numbering, SPI0)
#
#   TMC5160 SDI  (MOSI) ← GPIO 10  (physical pin 19)
#   TMC5160 SDO  (MISO) → GPIO  9  (physical pin 21)
#   TMC5160 SCK  (CLK)  ← GPIO 11  (physical pin 23)
#   TMC5160 CSN  (CS)   ← GPIO  8  (physical pin 24)  CE0
#   TMC5160 GND         ← GND (pin 39 or any GND)
#   TMC5160 VCC_IO      ← 3.3 V (pin 1 or 17)
#   TMC5160 VS          ← Motor supply (12–48 V)
#
# SPI0 is enabled by default via dtparam=spi=on in config.txt.
# Verify: ls /dev/spidev0.*   → should show spidev0.0
#
# SPI PROTOCOL (TMC5160)
#   Mode 3 (CPOL=1, CPHA=1): clock idles HIGH, data sampled on
#   the falling edge. spidev mode=3.
#   Frame: 5 bytes (40 bits), MSB-first.
#   Write: [reg|0x80, D31–D24, D23–D16, D15–D8, D7–D0]
#   Read:  TWO transactions.
#     Tx1: [reg, 0, 0, 0, 0]  — primes the output shift register
#     Tx2: [reg, 0, 0, 0, 0]  — clocks out data (bytes 1–4)
#   CS must de-assert (go HIGH) between Tx1 and Tx2.
#   xfer2() de-asserts CS after each call, so two calls = correct.
#
# QUICK WIRING CHECK
#   Read IOIN (0x04). Bits [31:24] = VERSION = 0x30 for TMC5160.
#   0x00 everywhere → MISO not connected or chip not powered.
#   0xFF everywhere → SPI bus floating (MISO stuck high).
# ============================================================

import sys
from enum import IntEnum
from typing import Optional

import spidev

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPI_BUS    = 0
SPI_DEVICE = 0
SPI_MODE   = 3           # CPOL=1, CPHA=1
SPI_MAX_HZ = 4_000_000   # 4 MHz — safe for bench testing (datasheet max 8 MHz)

TMC5160_VERSION = 0x30   # Expected IOIN bits [31:24]

# ---------------------------------------------------------------------------
# Register map
# ---------------------------------------------------------------------------

class Reg(IntEnum):
    GCONF      = 0x00
    GSTAT      = 0x01
    IOIN       = 0x04
    IHOLD_IRUN = 0x10
    TPOWERDOWN = 0x11
    RAMPMODE   = 0x20
    XACTUAL    = 0x21
    VMAX       = 0x27
    CHOPCONF   = 0x6C
    DRVSTATUS  = 0x6F
    PWMCONF    = 0x70

# ---------------------------------------------------------------------------
# Bit-field definitions: {field_name: (shift, mask)}
# ---------------------------------------------------------------------------

_GCONF_FIELDS: dict[str, tuple[int, int]] = {
    "recalibrate":    (0,  0x1),
    "faststandstill": (1,  0x1),
    "en_pwm_mode":    (2,  0x1),  # StealthChop enable
    "multistep_filt": (3,  0x1),
    "shaft":          (4,  0x1),  # Direction inversion
    "diag0_error":    (5,  0x1),
    "diag0_otpw":     (6,  0x1),
    "diag0_stall":    (7,  0x1),
    "diag1_stall":    (8,  0x1),
    "diag1_index":    (9,  0x1),
    "diag1_onstate":  (10, 0x1),
    "small_hysteresis":(14, 0x1),
    "stop_enable":    (15, 0x1),
    "direct_mode":    (16, 0x1),
}

_GSTAT_FIELDS: dict[str, tuple[int, int]] = {
    "reset":   (0, 0x1),  # Device was reset since last read
    "drv_err": (1, 0x1),  # Driver error (overtemp or short)
    "uv_cp":   (2, 0x1),  # Undervoltage on charge pump
}

_IOIN_FIELDS: dict[str, tuple[int, int]] = {
    "REFL_STEP":    (0,  0x1),
    "REFR_DIR":     (1,  0x1),
    "ENCB":         (2,  0x1),
    "ENCA":         (3,  0x1),
    "DRV_ENN":      (4,  0x1),
    "ENCN":         (5,  0x1),
    "UART_EN":      (6,  0x1),
    "COMP_A":       (8,  0x1),
    "COMP_B":       (9,  0x1),
    "COMP_A1A2":    (10, 0x1),
    "COMP_B1B2":    (11, 0x1),
    "OUTPUT":       (12, 0x1),
    "EXT_RES_DET":  (13, 0x1),
    "SILICON_RV":   (16, 0x7),
    "VERSION":      (24, 0xFF),
}

_CHOPCONF_FIELDS: dict[str, tuple[int, int]] = {
    "toff":    (0,  0xF),   # Off time; 0 = driver disabled
    "hstrt":   (4,  0x7),
    "hend":    (7,  0xF),
    "tbl":     (15, 0x3),   # Blank time
    "vsense":  (17, 0x1),   # Current sense voltage scaling
    "vhighfs": (18, 0x1),
    "vhighchm":(19, 0x1),
    "tpfd":    (20, 0xF),
    "mres":    (24, 0xF),   # Microstep resolution
    "intpol":  (28, 0x1),   # Interpolation to 256 microsteps
    "dedge":   (29, 0x1),
    "diss2g":  (30, 0x1),
    "diss2vs": (31, 0x1),
}

# Bit positions per TMC5160 datasheet Table 21.
# s2vsb/s2vsa (bits 26–25) exist on TMC5160A; may be reserved on TMC5160T.
_DRVSTATUS_FIELDS: dict[str, tuple[int, int]] = {
    "stst":      (31, 0x1),
    "olb":       (30, 0x1),
    "ola":       (29, 0x1),
    "s2gb":      (28, 0x1),
    "s2ga":      (27, 0x1),
    "s2vsb":     (26, 0x1),
    "s2vsa":     (25, 0x1),
    "ot":        (24, 0x1),   # Overtemperature
    "otpw":      (22, 0x1),   # Overtemp prewarning
    "cs_actual": (16, 0x1F),  # Bits [20:16]
    "fsactive":  (15, 0x1),
    "stealth":   (14, 0x1),
    "sg_result": (0,  0x3FF), # Bits [9:0]
}

_MRES_MAP: dict[int, int] = {
    256: 0, 128: 1, 64: 2, 32: 3,
    16:  4, 8:   5, 4:  6, 2:  7, 1: 8,
}
_MRES_REVERSE: dict[int, int] = {v: k for k, v in _MRES_MAP.items()}

# ---------------------------------------------------------------------------
# SPI transport
# ---------------------------------------------------------------------------

_spi: Optional[spidev.SpiDev] = None


def open_spi() -> None:
    global _spi
    try:
        _spi = spidev.SpiDev()
        _spi.open(SPI_BUS, SPI_DEVICE)
        _spi.max_speed_hz = SPI_MAX_HZ
        _spi.mode = SPI_MODE
        _spi.bits_per_word = 8
        _spi.no_cs = False
        print(f"Opened /dev/spidev{SPI_BUS}.{SPI_DEVICE}  mode={SPI_MODE}  {SPI_MAX_HZ // 1_000_000} MHz")
    except FileNotFoundError:
        print(
            f"ERROR: /dev/spidev{SPI_BUS}.{SPI_DEVICE} not found.\n"
            "  Verify 'dtparam=spi=on' is in /boot/firmware/config.txt and reboot."
        )
        sys.exit(1)
    except PermissionError:
        print(
            f"ERROR: Permission denied on /dev/spidev{SPI_BUS}.{SPI_DEVICE}.\n"
            "  Add user to spi group: sudo usermod -aG spi $USER  (then log out/in)"
        )
        sys.exit(1)


def close_spi() -> None:
    global _spi
    if _spi is not None:
        _spi.close()
        _spi = None


def _transfer(data: list[int]) -> list[int]:
    assert len(data) == 5, f"TMC5160 requires 5-byte frames, got {len(data)}"
    assert _spi is not None, "SPI not open — call open_spi() first"
    return _spi.xfer2(data)

# ---------------------------------------------------------------------------
# Register I/O
# ---------------------------------------------------------------------------

def read_register(reg: Reg) -> int:
    """
    Read a TMC5160 register via two 5-byte SPI transactions.

    Tx1 primes the TMC5160 output shift register with the addressed register.
    Tx2 clocks out the data. CS de-asserts between calls (xfer2 behaviour),
    which is required by the TMC5160 protocol to commit the address latch.
    """
    addr = int(reg) & 0x7F
    _transfer([addr, 0, 0, 0, 0])
    resp = _transfer([addr, 0, 0, 0, 0])
    return (resp[1] << 24) | (resp[2] << 16) | (resp[3] << 8) | resp[4]


def write_register(reg: Reg, value: int) -> None:
    addr = int(reg) | 0x80
    _transfer([
        addr,
        (value >> 24) & 0xFF,
        (value >> 16) & 0xFF,
        (value >>  8) & 0xFF,
        value         & 0xFF,
    ])

# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _parse_fields(raw: int, field_map: dict[str, tuple[int, int]]) -> dict:
    return {name: (raw >> shift) & mask for name, (shift, mask) in field_map.items()}


def get_gconf() -> dict:
    raw = read_register(Reg.GCONF)
    result = _parse_fields(raw, _GCONF_FIELDS)
    result["_raw"] = hex(raw)
    return result


def get_gstat() -> dict:
    """Read GSTAT. Note: reading this register clears all flags."""
    raw = read_register(Reg.GSTAT)
    result = _parse_fields(raw, _GSTAT_FIELDS)
    result["_raw"] = hex(raw)
    return result


def get_ioin() -> dict:
    raw = read_register(Reg.IOIN)
    result = _parse_fields(raw, _IOIN_FIELDS)
    result["_raw"] = hex(raw)
    return result


def get_driver_status() -> dict:
    raw = read_register(Reg.DRVSTATUS)
    result = _parse_fields(raw, _DRVSTATUS_FIELDS)
    result["_raw"] = hex(raw)
    return result


def get_chopconf() -> dict:
    raw = read_register(Reg.CHOPCONF)
    result = _parse_fields(raw, _CHOPCONF_FIELDS)
    result["microsteps"] = _MRES_REVERSE.get(result["mres"], "unknown")
    result["_raw"] = hex(raw)
    return result

# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def set_ihold_irun(ihold: int, irun: int, iholddelay: int = 6) -> None:
    """
    Set motor current.
      ihold:      0–31  hold current
      irun:       0–31  run current
      iholddelay: 0–15  delay before dropping to hold after standstill
    Safe test values: ihold=8, irun=16, iholddelay=6.
    """
    if not (0 <= ihold <= 31 and 0 <= irun <= 31 and 0 <= iholddelay <= 15):
        raise ValueError(f"Out of range: ihold={ihold}, irun={irun}, iholddelay={iholddelay}")
    value = (iholddelay << 16) | (irun << 8) | ihold
    write_register(Reg.IHOLD_IRUN, value)
    print(f"  IHOLD={ihold} IRUN={irun} IHOLDDELAY={iholddelay}  → 0x{value:08X}")


def set_chopconf_mres(microsteps: int) -> None:
    """Update only the mres bits [27:24] in CHOPCONF (read-modify-write)."""
    if microsteps not in _MRES_MAP:
        raise ValueError(f"microsteps must be one of {sorted(_MRES_MAP)}, got {microsteps}")
    mres_val = _MRES_MAP[microsteps]
    current = read_register(Reg.CHOPCONF)
    updated = (current & ~(0xF << 24)) | (mres_val << 24)
    write_register(Reg.CHOPCONF, updated)
    print(f"  CHOPCONF mres={microsteps} microsteps (field={mres_val})  → 0x{updated:08X}")

# ---------------------------------------------------------------------------
# Connection verification
# ---------------------------------------------------------------------------

def verify_connection() -> bool:
    ioin = get_ioin()
    version = ioin.get("VERSION", 0)
    if version == TMC5160_VERSION:
        print(f"  OK: TMC5160 detected  (IOIN.VERSION=0x{version:02X})")
        return True
    if version == 0x00:
        print(
            "  FAIL: IOIN.VERSION=0x00 — no response.\n"
            "  Check: MISO connected? VCC_IO powered? SPI mode 3?"
        )
    elif version == 0xFF:
        print(
            "  FAIL: IOIN.VERSION=0xFF — bus floating/stuck-high.\n"
            "  Check: MOSI/MISO/SCK connections and pull-ups."
        )
    elif version == 0x20:
        print(
            f"  WARN: IOIN.VERSION=0x20 — this may be a TMC5160A.\n"
            f"  Update TMC5160_VERSION=0x20 if that is your chip."
        )
    else:
        print(f"  WARN: IOIN.VERSION=0x{version:02X} — unexpected value.")
    return False

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _print_dict(d: dict) -> None:
    for k, v in d.items():
        print(f"    {k}: {v}")


def main() -> None:
    open_spi()

    try:
        print("\n--- Connection check (IOIN) ---")
        if not verify_connection():
            print("Aborting — fix wiring before continuing.")
            return

        print("\n--- GCONF ---")
        _print_dict(get_gconf())

        print("\n--- GSTAT (reading clears flags) ---")
        gstat = get_gstat()
        _print_dict(gstat)
        if gstat.get("reset"):
            print("    NOTE: driver was reset since last power-on or GSTAT read.")
        if gstat.get("drv_err"):
            print("    WARNING: driver error set — check DRVSTATUS.")

        print("\n--- CHOPCONF ---")
        _print_dict(get_chopconf())

        print("\n--- DRVSTATUS ---")
        drvstatus = get_driver_status()
        _print_dict(drvstatus)
        if drvstatus.get("ot"):
            print("    WARNING: overtemperature! Reduce current or improve cooling.")
        if drvstatus.get("s2ga") or drvstatus.get("s2gb"):
            print("    WARNING: short-to-GND detected on a motor coil.")

        print("\n--- Setting motor current ---")
        set_ihold_irun(ihold=8, irun=16, iholddelay=6)

        print("\n--- Enabling StealthChop (GCONF.en_pwm_mode = 1) ---")
        raw_gconf = read_register(Reg.GCONF)
        write_register(Reg.GCONF, raw_gconf | (1 << 2))
        print(f"    en_pwm_mode = {get_gconf()['en_pwm_mode']}")

        # Interactive loop
        _readable: dict[str, tuple] = {
            "gconf":     (get_gconf,         "General config"),
            "gstat":     (get_gstat,         "Global status (CLEAR ON READ)"),
            "ioin":      (get_ioin,          "Pin states + VERSION"),
            "chopconf":  (get_chopconf,      "Chopper config"),
            "drvstatus": (get_driver_status, "Driver status"),
            "rampmode":  (lambda: {"value": hex(read_register(Reg.RAMPMODE))}, "Ramp mode"),
            "xactual":   (lambda: {"value": read_register(Reg.XACTUAL)},       "Actual position"),
            "vmax":      (lambda: {"value": read_register(Reg.VMAX)},           "Max velocity"),
            "pwmconf":   (lambda: {"value": hex(read_register(Reg.PWMCONF))},  "StealthChop PWM config"),
        }

        print("\n--- Interactive register read ---")
        print("Registers: " + ", ".join(_readable))
        print("Commands:  <name>  |  q (quit)  |  help")

        while True:
            try:
                cmd = input("\ntmc5160> ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            if cmd in ("q", "quit", "exit"):
                break
            elif cmd in ("", "help", "?"):
                print("  Registers: " + ", ".join(_readable))
            elif cmd in _readable:
                fn, desc = _readable[cmd]
                print(f"  [{cmd.upper()}] {desc}")
                _print_dict(fn())
            else:
                print(f"  Unknown: '{cmd}'. Type 'help' for list.")

    finally:
        close_spi()
        print("SPI closed.")


if __name__ == "__main__":
    main()
