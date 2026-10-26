"""Section palette (Qt-free): section key -> (light, dark) hex colors, per gui.md."""

from agenda.gui.bar_model import PADDING

GRAY = "#8a8984"

# key -> (light, dark); padding is gray, the widget adds the 45 degree hatch
PALETTE: dict[str, tuple[str, str]] = {
    "front_back": (GRAY, GRAY),
    "monthly": ("#2a78d6", "#3987e5"),
    "weekly": ("#eb6834", "#d95926"),
    "daily": ("#1baf7a", "#199e70"),
    "optional": ("#6250d6", "#9085e9"),
    "value_added": ("#eda100", "#c98500"),
    PADDING: (GRAY, GRAY),
}


def section_color(key: str, dark: bool) -> str:
    """Hex color for a section key (or PADDING); unknown keys fall back to gray."""
    light, night = PALETTE.get(key, (GRAY, GRAY))
    return night if dark else light


def _luminance(hex_color: str) -> float:
    """WCAG relative luminance of '#rrggbb'."""
    chans = [int(hex_color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in chans]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def text_on(hex_color: str) -> str:
    """Black or white, whichever contrasts more with ``hex_color`` (legend chip labels)."""
    lum = _luminance(hex_color)
    return "#000000" if (lum + 0.05) / 0.05 >= 1.05 / (lum + 0.05) else "#ffffff"


def is_dark(window_lightness: int) -> bool:
    """True when the window background lightness (0-255) says dark mode."""
    return window_lightness < 128
