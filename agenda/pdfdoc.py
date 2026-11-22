"""``AgendaPDF``: the FPDF document of an agenda, with the per-font text color and size scale.

Pages pick a font through ``draw.set_font(pdf, role, style, size)``, which scales ``size`` by
``agenda_font_scale[role]`` and tells the document the current role. A role with a color in
``agenda_font_colors`` replaces plain text color (the palette ink, or black, the PDF default):
text a page draws in the accent, muted or any other color keeps it. The order of
``set_text_color`` and ``set_font`` calls does not matter, because the color the page asked for
is remembered separately from the one in effect.

With a scale above 100 %, ``cell`` shortens text that no longer fits its width with "…".
With the defaults (no colors, scale 1) the output is byte-identical to a plain FPDF.
"""

from __future__ import annotations

from typing import Any

from fpdf import FPDF

from agenda.day_extras import truncate

RGB = tuple[int, int, int]


def _rgb255(c: Any) -> RGB | None:
    """(r, g, b) 0-255 of an fpdf color (DeviceRGB/DeviceGray), None if unknown."""
    values = getattr(c, "colors255", None)
    if values is None:
        return None
    values = tuple(round(v) for v in values)
    return values * 3 if len(values) == 1 else values[:3]  # type: ignore[return-value]


class AgendaPDF(FPDF):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.agenda_font_scale: dict[str, float] = {}
        self.agenda_font_colors: dict[str, RGB] = {}
        self.agenda_ink: RGB = (0, 0, 0)
        self.agenda_font_role: str | None = None
        self._default_text = self.text_color
        self._asked_text: Any = None  # color the page last asked for (None = never: default)

    # --- per-font text color ---
    def set_text_color(self, r: Any, g: Any = -1, b: Any = -1) -> None:
        super().set_text_color(r, g, b)
        self._asked_text = self.text_color
        self._apply_font_color()

    def use_font_role(self, role: str) -> None:
        """Called by ``draw.set_font``: text from now on is drawn with font ``role``."""
        self.agenda_font_role = role
        self._apply_font_color()

    def _apply_font_color(self) -> None:
        if not self.agenda_font_colors:
            return
        asked = self._asked_text if self._asked_text is not None else self._default_text
        rgb = self.agenda_font_colors.get(self.agenda_font_role or "")
        if rgb is not None and _rgb255(asked) in {self.agenda_ink, (0, 0, 0)}:
            FPDF.set_text_color(self, *rgb)
        else:
            FPDF.set_text_color(self, asked)

    # --- size scale safety net ---
    def cell(self, w: Any = None, h: Any = None, text: str = "", *args: Any, **kwargs: Any) -> Any:
        if "txt" in kwargs:  # fpdf2's deprecated spelling
            text = kwargs.pop("txt")
        if text and w and w > 0 and max(self.agenda_font_scale.values(), default=1) > 1:
            room = w - 2 * self.c_margin
            if room > 0 and self.get_string_width(text) > room:
                text = truncate(text, room, self.get_string_width)
        return super().cell(w, h, text, *args, **kwargs)
