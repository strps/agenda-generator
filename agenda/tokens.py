"""Design tokens (mm unless noted): grid, spacing, type, strokes, radii."""

from __future__ import annotations

PT_TO_MM = 25.4 / 72

# Grid (layout-grid.md section 2)
COLUMNS = 6
GUTTER = 3.0
BASELINE = 5.0

# Page frame (section 1). Inner/outer margins come from Config.
MARGIN_TOP = 10.0
MARGIN_BOTTOM = 10.0
HEADER_HEIGHT = 12.0
FOOTER_HEIGHT = 6.0

SPACING = (1.0, 2.0, 3.0, 5.0, 8.0, 13.0)
TYPE_SIZES_PT = (6.0, 7.5, 9.0, 12.0, 18.0, 28.0)

STROKE_HAIRLINE = 0.15
STROKE_LIGHT = 0.25
STROKE_REGULAR = 0.4

RADII = (0.0, 1.0, 2.0)
DOT_SIZE = 0.35

# RGB colors (minimal theme defaults; themes.py may override)
COLORS = {
    "ink": (30, 30, 30),
    "muted": (120, 120, 120),
    "line": (190, 190, 190),
    "accent": (200, 80, 40),
    "tint": (240, 236, 232),
    "weekend_fill": (244, 242, 239),
    "holiday_fill": (247, 218, 205),
}


def pt_to_mm(pt: float) -> float:
    return pt * PT_TO_MM
