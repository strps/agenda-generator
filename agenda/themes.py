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
    # Feminine palettes: soft pastel fills with an accent dark enough for title text.
    "blush": {
        "ink": (45, 30, 35),
        "muted": (128, 100, 108),
        "line": (222, 196, 202),
        "accent": (196, 72, 108),
        "tint": (251, 236, 239),
        "weekend_fill": (252, 242, 244),
        "holiday_fill": (248, 214, 223),
    },
    "lavender": {
        "ink": (38, 32, 50),
        "muted": (112, 104, 132),
        "line": (206, 198, 224),
        "accent": (124, 82, 180),
        "tint": (241, 236, 250),
        "weekend_fill": (246, 243, 252),
        "holiday_fill": (224, 212, 244),
    },
    "peony": {
        "ink": (48, 28, 40),
        "muted": (130, 98, 116),
        "line": (226, 194, 210),
        "accent": (168, 44, 104),
        "tint": (250, 232, 241),
        "weekend_fill": (252, 241, 246),
        "holiday_fill": (244, 206, 226),
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


def normalize_hex(text: str) -> str:
    """ "#rgb"/"#rrggbb" (``#`` optional, any case) -> lowercase "#rrggbb"; else ValueError."""
    t = text.strip().lstrip("#")
    if len(t) == 3:
        t = "".join(c * 2 for c in t)
    if len(t) != 6 or any(c not in "0123456789abcdefABCDEF" for c in t):
        raise ValueError(f"not a hex color: {text!r}")
    return "#" + t.lower()


def hex_to_rgb(text: str) -> tuple[int, int, int]:
    t = normalize_hex(text)[1:]
    return int(t[0:2], 16), int(t[2:4], 16), int(t[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)
