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
#   TMC5160 ENN  (EN)   ← GPIO 27  (physical pin 13)  active-low
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
# VELOCITY CONTROL — TMC5160 vs TMC2209
#   On TMC2209 (UART driver), VACTUAL (0x22) is writable and
#   directly commands velocity. On TMC5160, VACTUAL is READ-ONLY
#   (it reports actual velocity from the ramp generator). To spin
#   the motor, set RAMPMODE=1 (CW) or 2 (CCW) and write VMAX.
#
# MOTOR DOESN'T SPIN — most common causes:
#   1. CHOPCONF.toff = 0 (reset default) → driver output disabled
#      Fix: write CHOPCONF with toff ≥ 1 (see init_driver())
#   2. DRV_ENN pin is HIGH (floating/undriven) → outputs disabled
#      Fix: drive GPIO 27 LOW (see enable_driver())
#   3. RAMPMODE not set to velocity mode → motor holds position
#      Fix: set RAMPMODE = 1 (CW) or 2 (CCW)
#   4. AMAX = 0 → acceleration is zero, motor never ramps up
#      Fix: write AMAX > 0 before setting VMAX
#
# QUICK WIRING CHECK
#   Read IOIN (0x04). Bits [31:24] = VERSION = 0x30 for TMC5160.
#   0x00 everywhere → MISO not connected or chip not powered.
#   0xFF everywhere → SPI bus floating (MISO stuck high).
# ============================================================

import sys
import time
from enum import IntEnum
from typing import Optional

import spidev

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Write-only registers on TMC5160 (SPI reads always return 0).
# Values written to these are shadowed in _write_cache for inspection.
_WRITE_ONLY_REGS = frozenset({
    0x23,  # VSTART
    0x24,  # A1
    0x25,  # V1
    0x26,  # AMAX
    0x28,  # DMAX
    0x2A,  # D1
    0x2B,  # VSTOP
    0x2C,  # TZEROWAIT
})

SPI_BUS    = 0
SPI_DEVICE = 0
SPI_MODE   = 3           # CPOL=1, CPHA=1
SPI_MAX_HZ = 4_000_000   # 4 MHz — safe for bench testing (datasheet max 8 MHz)

TMC5160_VERSION = 0x30   # Expected IOIN bits [31:24]
ENABLE_PIN_BCM  = 27     # GPIO for DRV_ENN — active-low (LOW = driver enabled)
TMC_CLK_HZ      = 12_000_000  # TMC5160 internal oscillator

# ---------------------------------------------------------------------------
# Register map
# ---------------------------------------------------------------------------

class Reg(IntEnum):
    GCONF      = 0x00
    GSTAT      = 0x01
    IOIN       = 0x04
    IHOLD_IRUN = 0x10
    TPOWERDOWN = 0x11
    RAMPMODE   = 0x20   # 0=positioning, 1=vel CW, 2=vel CCW, 3=hold
    XACTUAL    = 0x21   # Actual position counter (R/W)
    VACTUAL    = 0x22   # Actual velocity — READ ONLY on TMC5160
    VSTART     = 0x23   # Start velocity (write only)
    A1         = 0x24   # First acceleration (write only)
    V1         = 0x25   # First velocity threshold (write only)
    AMAX       = 0x26   # Maximum acceleration (write only)
    VMAX       = 0x27   # Maximum / target velocity
    DMAX       = 0x28   # Maximum deceleration (write only)
    D1         = 0x2A   # First deceleration (write only)
    VSTOP      = 0x2B   # Stop velocity (write only)
    XTARGET    = 0x2D   # Target position for positioning mode (R/W)
    CHOPCONF   = 0x6C
    DRVSTATUS  = 0x6F
    PWMCONF    = 0x70

# ---------------------------------------------------------------------------
# Bit-field definitions: {field_name: (shift, mask)}
# ---------------------------------------------------------------------------

_GCONF_FIELDS: dict[str, tuple[int, int]] = {
    "recalibrate":     (0,  0x1),
    "faststandstill":  (1,  0x1),
    "en_pwm_mode":     (2,  0x1),  # StealthChop enable
    "multistep_filt":  (3,  0x1),
    "shaft":           (4,  0x1),  # Invert positive direction
    "diag0_error":     (5,  0x1),
    "diag0_otpw":      (6,  0x1),
    "diag0_stall":     (7,  0x1),
    "diag1_stall":     (8,  0x1),
    "diag1_index":     (9,  0x1),
    "diag1_onstate":   (10, 0x1),
    "small_hysteresis":(14, 0x1),
    "stop_enable":     (15, 0x1),
    "direct_mode":     (16, 0x1),
}

_GSTAT_FIELDS: dict[str, tuple[int, int]] = {
    "reset":   (0, 0x1),  # Device was reset since last read
    "drv_err": (1, 0x1),  # Driver error (overtemp or short)
    "uv_cp":   (2, 0x1),  # Undervoltage on charge pump
}

_IOIN_FIELDS: dict[str, tuple[int, int]] = {
    "REFL_STEP":   (0,  0x1),
    "REFR_DIR":    (1,  0x1),
    "ENCB":        (2,  0x1),
    "ENCA":        (3,  0x1),
    "DRV_ENN":     (4,  0x1),  # 0 = driver enabled, 1 = disabled
    "ENCN":        (5,  0x1),
    "UART_EN":     (6,  0x1),
    "COMP_A":      (8,  0x1),
    "COMP_B":      (9,  0x1),
    "COMP_A1A2":   (10, 0x1),
    "COMP_B1B2":   (11, 0x1),
    "OUTPUT":      (12, 0x1),
    "EXT_RES_DET": (13, 0x1),
    "SILICON_RV":  (16, 0x7),
    "VERSION":     (24, 0xFF),
}

_CHOPCONF_FIELDS: dict[str, tuple[int, int]] = {
    "toff":    (0,  0xF),   # Off time; 0 = driver output disabled!
    "hstrt":   (4,  0x7),
    "hend":    (7,  0xF),
    "tbl":     (15, 0x3),   # Blank time
    "vsense":  (17, 0x1),   # 0 = low sensitivity (BTT Pro, external FETs)
    "vhighfs": (18, 0x1),
    "vhighchm":(19, 0x1),
    "tpfd":    (20, 0xF),
    "mres":    (24, 0xF),   # Microstep resolution
    "intpol":  (28, 0x1),   # Interpolation to 256 microsteps
    "dedge":   (29, 0x1),
    "diss2g":  (30, 0x1),
    "diss2vs": (31, 0x1),
}

# Per TMC5160 datasheet Table 21.
# s2vsb/s2vsa (bits 26–25) are TMC5160A only; may be reserved on TMC5160T.
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
    "cs_actual": (16, 0x1F),  # Bits [20:16] — actual current scale
    "fsactive":  (15, 0x1),
    "stealth":   (14, 0x1),
    "sg_result": (0,  0x3FF), # Bits [9:0] — StallGuard result
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
_write_cache: dict[int, int] = {}   # shadows write-only register values


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
    _write_cache[int(reg)] = value


def read_register_or_cached(reg: Reg) -> tuple[int, bool]:
    """
    Return (value, is_cached).
    For write-only registers, SPI reads always return 0; return the last
    written value from the cache instead and flag it as cached.
    """
    if int(reg) in _WRITE_ONLY_REGS:
        return _write_cache.get(int(reg), 0), True
    return read_register(reg), False

# ---------------------------------------------------------------------------
# GPIO — enable pin
# ---------------------------------------------------------------------------

_enable_gpio = None
_HAS_GPIO = False


def _init_gpio() -> None:
    global _enable_gpio, _HAS_GPIO
    try:
        from gpiozero import OutputDevice
        # active_high=False: .on() → GPIO LOW (DRV_ENN asserted = driver enabled)
        _enable_gpio = OutputDevice(ENABLE_PIN_BCM, active_high=False, initial_value=False)
        _HAS_GPIO = True
        print(f"GPIO ready  (enable pin BCM {ENABLE_PIN_BCM})")
    except Exception as e:
        print(f"WARNING: GPIO unavailable ({e}) — DRV_ENN pin not controlled.")
        print("  If the motor doesn't spin, manually pull GPIO 27 LOW.")


def enable_driver() -> None:
    """Assert DRV_ENN LOW to enable driver outputs."""
    if _HAS_GPIO and _enable_gpio is not None:
        _enable_gpio.on()   # active_high=False → drives GPIO LOW
        print("  Driver enabled  (DRV_ENN = LOW)")
    else:
        print("  GPIO not available — ensure DRV_ENN is pulled LOW externally.")


def disable_driver() -> None:
    """De-assert DRV_ENN (HIGH) to disable driver outputs."""
    if _HAS_GPIO and _enable_gpio is not None:
        _enable_gpio.off()  # active_high=False → drives GPIO HIGH
        print("  Driver disabled  (DRV_ENN = HIGH)")

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
      ihold:      0–31  hold current (fraction of IRUN)
      irun:       0–31  run current
      iholddelay: 0–15  delay before dropping to hold after standstill
    Safe test values: ihold=8, irun=16, iholddelay=6.
    """
    if not (0 <= ihold <= 31 and 0 <= irun <= 31 and 0 <= iholddelay <= 15):
        raise ValueError(f"Out of range: ihold={ihold}, irun={irun}, iholddelay={iholddelay}")
    value = (iholddelay << 16) | (irun << 8) | ihold
    write_register(Reg.IHOLD_IRUN, value)
    print(f"  IHOLD={ihold}  IRUN={irun}  IHOLDDELAY={iholddelay}  → 0x{value:08X}")


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
# Driver initialisation
# ---------------------------------------------------------------------------

# SpreadCycle CHOPCONF for BTT TMC5160 Pro (external MOSFETs, high-current):
#   toff=3  [3:0]   — chopper off time; MUST be ≥ 1 or outputs are disabled
#   hstrt=4 [6:4]   — hysteresis start
#   hend=1  [10:7]  — hysteresis end (field value, not physical offset)
#   tbl=2   [16:15] — blank time (36 clock cycles)
#   vsense=0 [17]   — full-range current sensing (required for external FETs)
#   mres=0  [27:24] — 256 microsteps
#   intpol=1 [28]   — interpolate to 256 for smoother motion
_CHOPCONF_INIT = (
    (3      )       |   # toff
    (4 <<  4)       |   # hstrt
    (1 <<  7)       |   # hend
    (2 << 15)       |   # tbl
    (0 << 17)       |   # vsense=0 (external FETs)
    (0 << 24)       |   # mres=0 (256 microsteps)
    (1 << 28)           # intpol
)   # = 0x100100C3


def init_driver(
    ihold: int = 8,
    irun: int  = 16,
    iholddelay: int = 6,
    amax: int = 500,
) -> None:
    """
    Configure the TMC5160 for velocity-mode operation.

    Call this once after verify_connection() and before enable_driver().
    Critically, this sets CHOPCONF.toff > 0, which enables driver outputs.
    Without this, the motor will never move regardless of VMAX.

    Args:
        ihold:      Hold current scale  0–31
        irun:       Run current scale   0–31
        iholddelay: Hold current delay  0–15
        amax:       Acceleration for velocity ramp (higher = snappier start)
    """
    print("  Initialising TMC5160...")

    # Clear any reset/error flags (read clears them)
    read_register(Reg.GSTAT)

    # GCONF: SpreadCycle (en_pwm_mode=0), no shaft inversion, standard defaults
    write_register(Reg.GCONF, 0x00000000)

    # CHOPCONF: enable chopper with SpreadCycle settings
    write_register(Reg.CHOPCONF, _CHOPCONF_INIT)
    print(f"  CHOPCONF = 0x{_CHOPCONF_INIT:08X}  (toff=3, SpreadCycle, 256µstep, intpol)")

    # Current
    set_ihold_irun(ihold, irun, iholddelay)

    # Power-down delay after standstill (~320 ms at 12 MHz)
    write_register(Reg.TPOWERDOWN, 0x20)

    # Ramp parameters: start in hold mode, set acceleration
    write_register(Reg.RAMPMODE, 3)   # Hold (no motion)
    write_register(Reg.VMAX,     0)
    write_register(Reg.AMAX,     amax)
    write_register(Reg.VSTART,   0)
    write_register(Reg.VSTOP,    10)  # Required for positioning mode; safe to set here

    print("  Init done.")

# ---------------------------------------------------------------------------
# Velocity control
# ---------------------------------------------------------------------------

def _rpm_to_vmax(rpm: float, steps_per_rev: int = 200, microsteps: int = 256) -> int:
    """
    Convert RPM to a VMAX register value.

    TMC5160 velocity unit: v[µsteps/s] = VMAX * f_CLK / 2^24
    Rearranged:            VMAX = v[µsteps/s] * 2^24 / f_CLK

    Example (256 microsteps, 200 steps/rev):
      1 RPM  → VMAX ≈  1 193
      10 RPM → VMAX ≈ 11 932
    """
    usteps_per_sec = rpm * steps_per_rev * microsteps / 60.0
    return round(usteps_per_sec * (2 ** 24) / TMC_CLK_HZ)


def set_velocity(
    rpm: float,
    direction: str = "CW",
    steps_per_rev: int = 200,
    microsteps: int = 256,
) -> None:
    """
    Spin the motor at the requested RPM in the given direction.

    On TMC5160, velocity is controlled by:
      1. RAMPMODE = 1 (positive / CW) or 2 (negative / CCW)
      2. VMAX = desired velocity in TMC5160 internal units

    VACTUAL (0x22) is READ-ONLY on TMC5160 — writing to it has no effect.

    Args:
        rpm:          Target speed in RPM (must be > 0)
        direction:    "CW" or "CCW"
        steps_per_rev: Full steps per motor revolution (200 for 1.8° stepper)
        microsteps:   Microstep setting configured in CHOPCONF
    """
    if rpm <= 0:
        raise ValueError("RPM must be positive — use stop_motor() to halt.")
    if direction.upper() not in ("CW", "CCW"):
        raise ValueError(f"direction must be 'CW' or 'CCW', got '{direction}'")

    vmax = _rpm_to_vmax(rpm, steps_per_rev, microsteps)
    rampmode = 1 if direction.upper() == "CW" else 2

    write_register(Reg.RAMPMODE, rampmode)
    write_register(Reg.VMAX, vmax)
    print(f"  Spinning {direction} at {rpm:.1f} RPM  (VMAX={vmax}, RAMPMODE={rampmode})")


def stop_motor() -> None:
    """Ramp down to zero and hold."""
    write_register(Reg.VMAX, 0)
    write_register(Reg.RAMPMODE, 3)  # Hold mode
    print("  Motor stopping  (VMAX=0, RAMPMODE=3 hold)")

# ---------------------------------------------------------------------------
# Reset detection
# ---------------------------------------------------------------------------

def check_reset() -> bool:
    """
    Read GSTAT.reset to detect whether the TMC5160 has reset since last check.
    Returns True if a reset occurred. Reading GSTAT clears the flag.

    The most common cause of an unexpected reset during operation is a voltage
    dip on VS (motor supply) below the UVLO threshold (~4.75 V). This happens
    when the ramp generator fires its first PWM pulse and the supply lacks
    sufficient bulk capacitance. After a reset, ALL registers revert to OTP
    defaults — notably CHOPCONF.toff=0, which disables driver outputs.

    Recovery: type 'reinit' in the interactive loop, then 'spin <rpm>'.
    Hardware fix: add ≥100 µF electrolytic capacitance close to the VS pin,
    and/or reduce IRUN to lower the initial current surge.
    """
    gstat_raw = read_register(Reg.GSTAT)
    reset  = bool((gstat_raw >> 0) & 1)
    drv_err = bool((gstat_raw >> 1) & 1)
    uv_cp   = bool((gstat_raw >> 2) & 1)

    if reset:
        print("\n  *** TMC5160 RESET DETECTED (GSTAT.reset=1) ***")
        print("  All registers have reverted to OTP defaults (CHOPCONF.toff=0 — driver disabled).")
        print("  Likely cause: VS supply dipped below UVLO (~4.75 V) when the ramp generator")
        print("  fired its first PWM pulse (high instantaneous current demand).")
        print("  Hardware fix: add ≥100 µF bulk capacitance on VS near the TMC5160.")
        print("  Software workaround: reduce IRUN — type 'reinit <irun>' (e.g. 'reinit 4').")
    if uv_cp:
        print("  WARNING: GSTAT.uv_cp=1 — charge pump undervoltage (VCC_IO too low?).")
    if drv_err:
        print("  WARNING: GSTAT.drv_err=1 — driver error flag set; check drvstatus.")
    return reset


# ---------------------------------------------------------------------------
# Connection verification
# ---------------------------------------------------------------------------

def verify_connection() -> bool:
    ioin = get_ioin()
    version = ioin.get("VERSION", 0)
    drv_enn = ioin.get("DRV_ENN", 1)

    if version == TMC5160_VERSION:
        print(f"  OK: TMC5160 detected  (IOIN.VERSION=0x{version:02X})")
        if drv_enn:
            print("  NOTE: IOIN.DRV_ENN=1 — driver outputs currently disabled.")
            print("        Call enable_driver() to pull GPIO 27 LOW.")
        return True

    if version == 0x00:
        print(
            "  FAIL: IOIN.VERSION=0x00 — no response.\n"
            "  Check: MISO connected? VCC_IO powered? SPI mode 3?"
        )
    elif version == 0xFF:
        print(
            "  FAIL: IOIN.VERSION=0xFF — bus floating/stuck-high.\n"
            "  Check: MOSI/MISO/SCK connections."
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

DEFAULT_RPM        = 10
DEFAULT_STEPS_REV  = 200
DEFAULT_MICROSTEPS = 256


def _print_dict(d: dict) -> None:
    for k, v in d.items():
        print(f"    {k}: {v}")


def _help(commands: list[str]) -> None:
    print("  Register reads (R/W): " + ", ".join([
        "gconf", "gstat", "ioin", "chopconf", "drvstatus",
        "rampmode", "xactual", "vactual", "vmax", "pwmconf",
    ]))
    print("  Register reads (write-only, cached*): " + ", ".join([
        "amax", "vstart", "vstop", "a1", "v1", "dmax", "d1",
    ]))
    print("  *Write-only regs always read 0 via SPI; cached = last value written this session.")
    print("  Commands: " + ", ".join(commands))
    print("  reinit [irun]: re-write all config registers after a chip reset (default irun=8)")


def main() -> None:
    _init_gpio()
    open_spi()

    try:
        # ── 1. Verify connection ──────────────────────────────────────────────
        print("\n--- Connection check (IOIN) ---")
        if not verify_connection():
            print("Aborting — fix wiring before continuing.")
            return

        # ── 2. Initialise driver registers ───────────────────────────────────
        print("\n--- Driver initialisation ---")
        init_driver(ihold=8, irun=16, iholddelay=6, amax=500)

        # ── 3. Enable driver (assert DRV_ENN LOW via GPIO 27) ────────────────
        print("\n--- Enabling driver ---")
        enable_driver()

        # ── 4. Dump initial register state ───────────────────────────────────
        print("\n--- GSTAT (reading clears flags) ---")
        gstat = get_gstat()
        _print_dict(gstat)
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

        # ── 5. Start spinning ────────────────────────────────────────────────
        print(f"\n--- Starting motor at {DEFAULT_RPM} RPM CW ---")
        set_velocity(DEFAULT_RPM, direction="CW",
                     steps_per_rev=DEFAULT_STEPS_REV, microsteps=DEFAULT_MICROSTEPS)

        # Brief delay so the first PWM pulse can fire before we check GSTAT.
        time.sleep(0.1)
        check_reset()

        # ── 6. Interactive loop ───────────────────────────────────────────────
        motion_cmds = ["spin <rpm> [cw|ccw]", "stop", "reinit [irun]", "enable", "disable", "q"]

        print("\n--- Interactive control ---")
        _help(motion_cmds)

        while True:
            try:
                raw = input("\ntmc5160> ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                break

            parts = raw.lower().split()
            if not parts:
                _help(motion_cmds)
                continue
            cmd = parts[0]

            # --- Motion commands ---
            if cmd in ("q", "quit", "exit"):
                break

            elif cmd == "stop":
                stop_motor()

            elif cmd == "spin":
                try:
                    rpm = float(parts[1]) if len(parts) > 1 else DEFAULT_RPM
                    direction = parts[2].upper() if len(parts) > 2 else "CW"
                    set_velocity(rpm, direction,
                                 steps_per_rev=DEFAULT_STEPS_REV,
                                 microsteps=DEFAULT_MICROSTEPS)
                    time.sleep(0.1)
                    check_reset()
                except (ValueError, IndexError) as e:
                    print(f"  Usage: spin <rpm> [cw|ccw]   ({e})")

            elif cmd == "reinit":
                # Allow 'reinit <irun>' to test with lower current after a reset
                try:
                    irun = int(parts[1]) if len(parts) > 1 else 8
                    if not 0 <= irun <= 31:
                        raise ValueError("irun must be 0–31")
                except ValueError as e:
                    print(f"  Usage: reinit [irun 0–31]  ({e})")
                    irun = 8
                print(f"\n--- Reinitialising (IRUN={irun}) ---")
                init_driver(ihold=max(irun // 2, 1), irun=irun, iholddelay=6, amax=200)
                enable_driver()
                print("  Ready. Type 'spin <rpm>' to try again.")

            elif cmd == "enable":
                enable_driver()

            elif cmd == "disable":
                stop_motor()
                disable_driver()

            elif cmd == "help":
                _help(motion_cmds)

            # --- Register reads ---
            elif cmd == "gconf":
                _print_dict(get_gconf())
            elif cmd == "gstat":
                _print_dict(get_gstat())
            elif cmd == "ioin":
                ioin = get_ioin()
                _print_dict(ioin)
                if ioin.get("DRV_ENN"):
                    print("    NOTE: DRV_ENN=1 — driver disabled. Type 'enable' to fix.")
            elif cmd == "chopconf":
                cc = get_chopconf()
                _print_dict(cc)
                if cc.get("toff") == 0:
                    print("    *** toff=0: driver outputs DISABLED — chip likely reset.")
                    print("        Run 'gstat' to check reset flag, then 'reinit' to recover.")
            elif cmd == "drvstatus":
                drvs = get_driver_status()
                _print_dict(drvs)
                if drvs.get("ot"):
                    print("    WARNING: overtemperature!")
                if drvs.get("s2ga") or drvs.get("s2gb"):
                    print("    WARNING: short-to-GND on motor coil!")
            elif cmd == "rampmode":
                val = read_register(Reg.RAMPMODE)
                labels = {0: "positioning", 1: "velocity CW", 2: "velocity CCW", 3: "hold"}
                print(f"    RAMPMODE = {val} ({labels.get(val, 'unknown')})")
            elif cmd == "xactual":
                print(f"    XACTUAL = {read_register(Reg.XACTUAL)}")
            elif cmd == "vactual":
                print(f"    VACTUAL = {read_register(Reg.VACTUAL)}  (read-only actual velocity)")
            elif cmd == "vmax":
                vmax = read_register(Reg.VMAX)
                rpm_est = vmax * TMC_CLK_HZ / (2**24) / (DEFAULT_STEPS_REV * DEFAULT_MICROSTEPS) * 60
                print(f"    VMAX = {vmax}  (~{rpm_est:.1f} RPM at {DEFAULT_STEPS_REV} steps, {DEFAULT_MICROSTEPS} µsteps)")
            elif cmd in ("amax", "vstart", "vstop", "a1", "v1", "dmax", "d1"):
                reg_map = {
                    "amax":   Reg.AMAX,
                    "vstart": Reg.VSTART,
                    "vstop":  Reg.VSTOP,
                    "a1":     Reg.A1,
                    "v1":     Reg.V1,
                    "dmax":   Reg.DMAX,
                    "d1":     Reg.D1,
                }
                r = reg_map[cmd]
                val, cached = read_register_or_cached(r)
                tag = "cached — write-only reg, SPI readback always 0" if cached else ""
                print(f"    {cmd.upper()} = {val}  {tag}")
            elif cmd == "pwmconf":
                print(f"    PWMCONF = {hex(read_register(Reg.PWMCONF))}")

            else:
                print(f"  Unknown command: '{cmd}'. Type 'help'.")

    finally:
        stop_motor()
        disable_driver()
        close_spi()
        print("Done.")


if __name__ == "__main__":
    main()
