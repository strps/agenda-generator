"""Application look (Qt-free): theme tokens, QSS builder, contrast helper, appearance choice."""

from __future__ import annotations

from pathlib import Path

from agenda.gui.section_colors import is_dark
from agenda.tokens import COLORS

APPEARANCES = ("dark", "light", "system")
DEFAULT_APPEARANCE = "dark"
SPACING = {"gap": 8, "margin": 12, "pad": 6, "radius": 4}
ICONS = Path(__file__).parent / "icons"

REQUIRED_TOKENS = (
    "window", "panel", "text", "muted", "border", "accent", "accent_text",
    "input_bg", "selection", "error", "tooltip_bg", "tooltip_text",
)  # fmt: skip


def _hex(rgb: tuple[int, ...]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb[:3])


def _lighten(rgb: tuple[int, ...], amount: float) -> tuple[int, ...]:
    return tuple(round(c + (255 - c) * amount) for c in rgb[:3])


_ACCENT_LIGHT = _hex(COLORS["accent"])
_ACCENT_DARK = _hex(_lighten(COLORS["accent"], 0.3))

THEMES: dict[str, dict[str, str]] = {
    "dark": {
        "window": "#1b1c1e",
        "panel": "#242528",
        "text": "#e6e6e3",
        "muted": "#9c9c97",
        "border": "#37393d",
        "accent": _ACCENT_DARK,
        "accent_text": "#1b1c1e",
        "input_bg": "#2d2f33",
        "selection": "#3d4048",
        "error": "#ff8f86",
        "tooltip_bg": "#2d2f33",
        "tooltip_text": "#e6e6e3",
    },
    "light": {
        "window": "#f5f5f3",
        "panel": "#ebebe8",
        "text": "#1c1c1b",
        "muted": "#5c5c58",
        "border": "#d4d4cf",
        "accent": _ACCENT_LIGHT,
        "accent_text": "#ffffff",
        "input_bg": "#ffffff",
        "selection": "#dcdcd7",
        "error": "#b3261e",
        "tooltip_bg": "#ffffff",
        "tooltip_text": "#1c1c1b",
    },
}


def _channel(v: int) -> float:
    c = v / 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _luminance(h: str) -> float:
    r, g, b = (int(h[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)


def contrast_ratio(hex_a: str, hex_b: str) -> float:
    """WCAG 2 contrast ratio (1..21) between two #rrggbb colors."""
    la, lb = _luminance(hex_a), _luminance(hex_b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def resolve_dark(appearance: str, window_lightness: int) -> bool:
    """Dark or light for an appearance choice; "system" follows the window lightness."""
    if appearance not in APPEARANCES:
        appearance = DEFAULT_APPEARANCE
    if appearance == "system":
        return is_dark(window_lightness)
    return appearance == "dark"


def stylesheet(dark: bool) -> str:
    """Flat QSS for the whole application."""
    t = THEMES["dark" if dark else "light"]
    gap, margin, pad, radius = (SPACING[k] for k in ("gap", "margin", "pad", "radius"))
    inputs = "QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit"
    check = (ICONS / f"check_{'dark' if dark else 'light'}.svg").as_posix()
    return f"""
QMainWindow, QWidget {{ background-color: {t["window"]}; color: {t["text"]}; }}
QWidget:disabled {{ color: {t["muted"]}; }}
QScrollArea {{ border: none; background-color: {t["window"]}; }}
QFrame#settings {{ border: none; background-color: {t["window"]}; }}
QFrame[objectName^="section_"] {{
    background-color: {t["panel"]}; border: 1px solid transparent; border-radius: {radius}px;
    margin: {gap // 2}px {margin // 2}px;
}}
QFrame[objectName^="section_"][active="true"] {{ border: 1px solid {t["accent"]}; }}
QFrame[objectName^="section_"] > QWidget {{ background-color: transparent; }}
QWidget#section_body {{ background-color: transparent; }}
QPushButton#group_toggle {{
    background-color: transparent; border: none; color: {t["muted"]}; font-weight: bold;
    padding: {pad}px {gap}px; margin-top: {gap}px; text-align: left;
}}
QPushButton#group_toggle:hover, QPushButton#group_toggle:focus {{ color: {t["text"]}; }}
QPushButton#group_toggle:checked, QPushButton#group_toggle:pressed {{
    background-color: transparent; border: none;
}}
QPushButton#section_toggle {{
    background-color: transparent; border: none; font-weight: bold;
    padding: {pad}px {gap}px; text-align: left;
}}
QPushButton#section_toggle:hover, QPushButton#section_toggle:checked,
QPushButton#section_toggle:pressed {{ background-color: transparent; border: none; }}
QFrame#collapsible_header {{ background-color: transparent; border-radius: {radius}px; }}
QFrame#collapsible_header:hover {{ background-color: {t["selection"]}; }}
QPushButton#section_toggle[active="true"] {{ color: {t["accent"]}; }}
QCheckBox#section_enable {{ background-color: transparent; spacing: {gap}px; }}
QCheckBox::indicator {{
    width: 14px; height: 14px; background-color: {t["input_bg"]};
    border: 1px solid {t["muted"]}; border-radius: {radius // 2}px;
}}
QCheckBox::indicator:hover {{ border: 1px solid {t["accent"]}; }}
QCheckBox::indicator:checked {{
    background-color: {t["accent"]}; border: 1px solid {t["accent"]}; image: url({check});
}}
QCheckBox::indicator:disabled {{ background-color: {t["panel"]}; border: 1px solid {t["border"]}; }}
QCheckBox::indicator:checked:disabled {{ background-color: {t["border"]}; }}
QPushButton {{
    background-color: {t["input_bg"]}; color: {t["text"]}; border: 1px solid {t["border"]};
    border-radius: {radius}px; padding: {pad}px {margin}px;
}}
QPushButton:hover {{ background-color: {t["selection"]}; }}
QPushButton:pressed {{ background-color: {t["border"]}; }}
QPushButton:checked {{ background-color: {t["selection"]}; border: 1px solid {t["accent"]}; }}
QPushButton:disabled {{ color: {t["muted"]}; background-color: {t["panel"]}; }}
QPushButton#export_button {{
    background-color: {t["accent"]}; color: {t["accent_text"]}; border: none; font-weight: bold;
}}
QPushButton#export_button:hover {{ background-color: {t["accent"]}; }}
QPushButton#export_button:disabled {{ background-color: {t["panel"]}; color: {t["muted"]}; }}
{inputs} {{
    background-color: {t["input_bg"]}; color: {t["text"]}; border: 1px solid {t["border"]};
    border-radius: {radius}px; padding: {pad}px; selection-background-color: {t["accent"]};
    selection-color: {t["accent_text"]};
}}
{inputs.replace(", ", ":disabled, ")}:disabled {{ color: {t["muted"]}; background-color: {t["panel"]}; }}
QGroupBox {{
    background-color: transparent; border: 1px solid {t["border"]}; border-radius: {radius}px;
    margin-top: {margin}px; padding: {pad}px;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: {gap}px; padding: 0 {pad}px; color: {t["muted"]}; }}
QProgressBar {{
    background-color: {t["panel"]}; border: none; border-radius: {radius}px; text-align: center;
}}
QProgressBar::chunk {{ background-color: {t["accent"]}; border-radius: {radius}px; }}
QToolTip {{
    background-color: {t["tooltip_bg"]}; color: {t["tooltip_text"]}; border: 1px solid {t["border"]};
    padding: {pad}px;
}}
QLabel#settings_error {{ color: {t["error"]}; padding: {pad}px {gap}px; }}
QLabel#legend_title {{ color: {t["muted"]}; font-weight: bold; }}
QLabel[objectName^="template_notice_"] {{ color: {t["muted"]}; padding: {pad}px {gap}px; }}
"""
