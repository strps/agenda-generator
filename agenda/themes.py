"""Named output palettes (Qt-free, no Config import).

A palette maps the token color names (``tokens.COLORS``) to RGB tuples. The selected palette is
carried on each FPDF document (``pdf.agenda_palette``) and read through ``draw.color``; the global
``tokens.COLORS`` is never mutated, so previews can render concurrently in worker threads.
"""

from __future__ import annotations

from agenda import tokens

Palette = dict[str, tuple[int, int, int]]

THEMES: dict[str, Palette] = {
    "minimal": dict(tokens.COLORS),
    "mono": {
        "ink": (20, 20, 20),
        "muted": (100, 100, 100),
        "line": (190, 190, 190),
        "accent": (60, 60, 60),
        "tint": (236, 236, 236),
        "weekend_fill": (242, 242, 242),
        "holiday_fill": (218, 218, 218),
    },
    "ocean": {
        "ink": (20, 30, 45),
        "muted": (95, 110, 125),
        "line": (185, 195, 205),
        "accent": (30, 90, 170),
        "tint": (230, 238, 247),
        "weekend_fill": (240, 244, 249),
        "holiday_fill": (208, 224, 244),
    },
    "forest": {
        "ink": (25, 35, 28),
        "muted": (98, 112, 100),
        "line": (188, 198, 188),
        "accent": (35, 105, 60),
        "tint": (232, 240, 233),
        "weekend_fill": (241, 245, 241),
        "holiday_fill": (210, 230, 214),
    },
}


def is_known(theme: str) -> bool:
    return theme in THEMES


def palette_for(theme: str, overrides: dict[str, tuple[int, int, int]] | None = None) -> Palette:
    """Copy of the named palette (unknown names give "minimal"), with ``overrides`` applied."""
    palette = dict(THEMES.get(theme, THEMES["minimal"]))
    for name, rgb in (overrides or {}).items():
        if name in palette:
            palette[name] = rgb
    return palette
