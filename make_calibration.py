"""
Generate calibration and measurement images for the OpenCAL projector.

Display each image fullscreen, measure with calipers, then use the known
fractions to calculate the actual projected width and height in mm.

Images generated
----------------
dark.png               Solid black — used as a blank/reset
cal_1_full_extent.png  White border on black: measure inside edges = full projected size
cal_2_checkerboard.png 4×4 checkerboard: one square = 25% of W × 25% of H
cal_3_crosshair.png    Centre lines + corner squares: measure half-dimensions
cal_4_grid_10pct.png   Grid lines every 10%: measure any span of N lines × 10% each

Usage
-----
python make_calibration.py
"""

from pathlib import Path
from PIL import Image, ImageDraw

W, H = 1920, 1080
OUT = Path("opencal/utils/calibration")
OUT.mkdir(parents=True, exist_ok=True)


def _save(img: Image.Image, name: str) -> None:
    path = OUT / name
    img.save(path)
    print(f"  {path}")


def _black() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (W, H), "black")
    return img, ImageDraw.Draw(img)


# ── dark ─────────────────────────────────────────────────────────────────────

def make_dark() -> None:
    img, _ = _black()
    _save(img, "dark.png")


# ── 1: full extent ────────────────────────────────────────────────────────────

def make_full_extent() -> None:
    """White 5px border outlining the exact edges of the projected frame."""
    img, draw = _black()
    draw.rectangle([0, 0, W - 1, H - 1], outline="white", width=5)
    _save(img, "cal_1_full_extent.png")


# ── 2: 4×4 checkerboard ───────────────────────────────────────────────────────

def make_checkerboard() -> None:
    """4 columns × 4 rows of alternating squares.

    Each square is exactly W/4 × H/4 pixels.
    Measure one square with calipers → multiply by 4 for full projected size.
    """
    img, draw = _black()
    cw, ch = W // 4, H // 4
    for r in range(4):
        for c in range(4):
            if (r + c) % 2 == 0:
                draw.rectangle(
                    [c * cw, r * ch, (c + 1) * cw - 1, (r + 1) * ch - 1],
                    fill="white",
                )
    _save(img, "cal_2_checkerboard.png")


# ── 3: crosshair ─────────────────────────────────────────────────────────────

def make_crosshair() -> None:
    """Vertical + horizontal centre lines and 50×50 px squares at each corner.

    - Measure corner square to outer edge → distance from corner to centre line
      = half the projected width / height.
    - Corner squares are solid white, easy to locate with calipers.
    """
    img, draw = _black()

    # Centre lines
    draw.line([(W // 2, 0), (W // 2, H - 1)], fill="white", width=3)
    draw.line([(0, H // 2), (W - 1, H // 2)], fill="white", width=3)

    # 50×50 corner squares at the four corners
    s = 50
    corners = [(0, 0), (W - s, 0), (0, H - s), (W - s, H - s)]
    for x, y in corners:
        draw.rectangle([x, y, x + s - 1, y + s - 1], fill="white")

    # Small circle at dead centre
    r = 15
    cx, cy = W // 2, H // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill="white")

    _save(img, "cal_3_crosshair.png")


# ── 4: 10% grid ──────────────────────────────────────────────────────────────

def make_grid_10pct() -> None:
    """Grid lines at every 10% of width and height.

    The centre lines (50%) are drawn 3px wide; all others 1px.
    Measure the distance between any two adjacent lines to get 10% of the
    projected dimension, then multiply by 10 for the full size.
    """
    img, draw = _black()
    for i in range(11):
        x = int(W * i / 10)
        y = int(H * i / 10)
        w = 3 if i == 5 else 1
        draw.line([(x, 0), (x, H - 1)], fill="white", width=w)
        draw.line([(0, y), (W - 1, y)], fill="white", width=w)
    _save(img, "cal_4_grid_10pct.png")


# ── main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating calibration images...")
    make_dark()
    make_full_extent()
    make_checkerboard()
    make_crosshair()
    make_grid_10pct()
    print("\nDone. Display each image fullscreen on the projector and measure:")
    print("  cal_1: inside of white border  → full W × H")
    print("  cal_2: one checkerboard square → W/4 × H/4  (×4 = full size)")
    print("  cal_3: corner square to centre → W/2 × H/2  (×2 = full size)")
    print("  cal_4: gap between any 2 lines → 10% of W or H (×10 = full size)")
