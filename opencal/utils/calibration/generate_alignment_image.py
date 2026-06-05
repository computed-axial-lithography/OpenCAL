"""
generate_alignment_image.py

Renders the cross strut alignment tool DXF as a 1920×1080 projector image.

At 90 µm/pixel the DXF geometry (in mm) is converted to pixels and centred
on the canvas.  All VISIBLE-layer entities (LINEs, ARCs, CIRCLEs) are drawn
in white on black so the projected image can be overlaid on the physical tool
to verify alignment.

Usage
-----
    pip install ezdxf          # once
    python generate_alignment_image.py [path/to/file.dxf]

The output PNG is written next to this script as  alignment_tool.png
and is automatically picked up by the Calibration menu in the LCD GUI.
"""

import math
import sys
from pathlib import Path

try:
    import ezdxf
except ImportError:
    print("ERROR: ezdxf not installed.  Run:  pip install ezdxf")
    sys.exit(1)

from PIL import Image, ImageDraw

# ── Configuration ────────────────────────────────────────────────────────────

PIXEL_SIZE_MM = 0.0801        # 80.1 µm per pixel — measured: 86.47mm / 1080px
PX_PER_MM     = 1.0 / PIXEL_SIZE_MM

# Projector is mounted 90° on its side — generate on portrait canvas, rotate for output.
W, H          = 1080, 1920
W_OUT, H_OUT  = 1920, 1080

LINE_WIDTH    = 2             # px — outline stroke
HOLE_WIDTH    = 3             # px — alignment hole stroke (slightly bolder)
ARC_STEPS     = 120           # line segments per arc

OUT_PATH = Path(__file__).parent / "alignment_tool.png"

# ── DXF path ─────────────────────────────────────────────────────────────────

if len(sys.argv) > 1:
    DXF_PATH = Path(sys.argv[1])
else:
    # Default: look next to this script
    DXF_PATH = Path(__file__).parent / "Cross Strut - Cross Strut.dxf"

if not DXF_PATH.exists():
    print(f"ERROR: DXF file not found: {DXF_PATH}")
    print("Usage: python generate_alignment_image.py <path/to/file.dxf>")
    sys.exit(1)

# ── Coordinate helpers ────────────────────────────────────────────────────────

# DXF origin → canvas centre; Y axis flipped (DXF Y+ = up, image Y+ = down)
cx_px = W / 2
cy_px = H / 2


def to_px(x_mm: float, y_mm: float) -> tuple[float, float]:
    return cx_px + x_mm * PX_PER_MM, cy_px - y_mm * PX_PER_MM


# ── Rendering helpers ─────────────────────────────────────────────────────────

def draw_line(draw: ImageDraw.ImageDraw, x1, y1, x2, y2, width=LINE_WIDTH) -> None:
    draw.line([(x1, y1), (x2, y2)], fill="white", width=width)


def draw_circle(draw: ImageDraw.ImageDraw, cx, cy, r_px, width=LINE_WIDTH) -> None:
    draw.ellipse([cx - r_px, cy - r_px, cx + r_px, cy + r_px],
                 outline="white", width=width)


def draw_arc(draw: ImageDraw.ImageDraw,
             cx, cy, r_px,
             start_deg: float, end_deg: float,
             width=LINE_WIDTH) -> None:
    """Draw a DXF arc (CCW from start_deg to end_deg) as polyline segments."""
    # Normalise so the arc always goes CCW
    if end_deg <= start_deg:
        end_deg += 360.0
    span = end_deg - start_deg
    pts = []
    for i in range(ARC_STEPS + 1):
        angle = math.radians(start_deg + span * i / ARC_STEPS)
        # DXF angles: 0° = +X, increases CCW; image Y is flipped → negate angle
        px = cx + r_px * math.cos(angle)
        py = cy - r_px * math.sin(angle)
        pts.append((px, py))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill="white", width=width)


# ── Filled slot helper ────────────────────────────────────────────────────────

def _fill_slot_v(draw: ImageDraw.ImageDraw,
                 x_mm: float, y_inner_mm: float, y_outer_mm: float, r_mm: float) -> None:
    """Fill a vertical rounded slot (rectangle + two semicircles)."""
    px, py_inner = to_px(x_mm, y_inner_mm)
    _,  py_outer = to_px(x_mm, y_outer_mm)
    r = r_mm * PX_PER_MM
    y_lo, y_hi = min(py_inner, py_outer), max(py_inner, py_outer)
    draw.rectangle([px - r, y_lo, px + r, y_hi], fill="white")
    draw.ellipse([px - r, py_inner - r, px + r, py_inner + r], fill="white")
    draw.ellipse([px - r, py_outer - r, px + r, py_outer + r], fill="white")


def _fill_slot_h(draw: ImageDraw.ImageDraw,
                 x_inner_mm: float, x_outer_mm: float, y_mm: float, r_mm: float) -> None:
    """Fill a horizontal rounded slot (rectangle + two semicircles)."""
    px_inner, py = to_px(x_inner_mm, y_mm)
    px_outer, _  = to_px(x_outer_mm, y_mm)
    r = r_mm * PX_PER_MM
    x_lo, x_hi = min(px_inner, px_outer), max(px_inner, px_outer)
    draw.rectangle([x_lo, py - r, x_hi, py + r], fill="white")
    draw.ellipse([px_inner - r, py - r, px_inner + r, py + r], fill="white")
    draw.ellipse([px_outer - r, py - r, px_outer + r, py + r], fill="white")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Reading DXF: {DXF_PATH}")
    doc = ezdxf.readfile(str(DXF_PATH))
    msp = doc.modelspace()

    img  = Image.new("RGB", (W, H), "black")
    draw = ImageDraw.Draw(img)

    lines   = 0
    arcs    = 0
    circles = 0

    for entity in msp:
        layer = entity.dxf.layer if entity.dxf.hasattr("layer") else ""
        if layer not in ("VISIBLE", ""):
            continue  # skip construction/annotation layers

        etype = entity.dxftype()

        if etype == "LINE":
            s  = entity.dxf.start
            e  = entity.dxf.end
            x1, y1 = to_px(s.x, s.y)
            x2, y2 = to_px(e.x, e.y)
            draw_line(draw, x1, y1, x2, y2)
            lines += 1

        elif etype == "ARC":
            c   = entity.dxf.center
            r   = entity.dxf.radius * PX_PER_MM
            sa  = entity.dxf.start_angle
            ea  = entity.dxf.end_angle
            px, py = to_px(c.x, c.y)
            draw_arc(draw, px, py, r, sa, ea)
            arcs += 1

        elif etype == "CIRCLE":
            c  = entity.dxf.center
            r  = entity.dxf.radius * PX_PER_MM
            px, py = to_px(c.x, c.y)
            # Alignment holes filled solid white for clear projection
            draw.ellipse([px - r, py - r, px + r, py + r], fill="white")
            circles += 1

    print(f"  Lines: {lines}  Arcs: {arcs}  Circles: {circles}")

    # Fill the 4 elongated alignment slots (stadium shapes from DXF geometry)
    _fill_slot_v(draw, x_mm=0,   y_inner_mm=14,   y_outer_mm=49.487,  r_mm=1.0)  # top
    _fill_slot_v(draw, x_mm=0,   y_inner_mm=-14,  y_outer_mm=-49.487, r_mm=1.0)  # bottom
    _fill_slot_h(draw, x_inner_mm=14,  x_outer_mm=32,  y_mm=0, r_mm=1.0)          # right
    _fill_slot_h(draw, x_inner_mm=-14, x_outer_mm=-32, y_mm=0, r_mm=1.0)          # left
    print("  Filled 4 alignment slots")

    img = img.rotate(-90, expand=True)
    img.save(OUT_PATH)
    print(f"Saved: {OUT_PATH}")
    print(f"Canvas: {W_OUT}×{H_OUT} px  |  Scale: {PX_PER_MM:.2f} px/mm  ({PIXEL_SIZE_MM*1000:.1f} µm/pixel)")


if __name__ == "__main__":
    main()
