"""Idea map page."""

from __future__ import annotations

import math
from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import BasePage, Ctx


class IdeaLayout(NamedTuple):
    centre: tuple[float, float]  # centre of the main shape, relative to the area's top-left
    centre_radii: tuple[float, float]  # (rx, ry) of the main ellipse
    sat_radii: tuple[float, float]  # (rx, ry) of every satellite ellipse
    satellites: list[tuple[float, float]]  # satellite centres, same origin, clockwise from top


@register
class IdeaMap(BasePage):
    """Idea map (mind map), ``count`` pages (default 1; id ``ideas``, value score 3).

    The catalog gives no repetition, so ``IdeaMap(count=N)`` gives N pages like Todo and Travel.
    Header with the title, then a canvas filling the content box: a central ellipse labelled
    "Main idea" with a write-in rule, and satellite ellipses, each joined to the centre by a
    line and holding a short write-in rule.

    Layout rule (``layout(w, h)``, all ratios of the canvas ``w`` x ``h``, no millimetres):
    satellites sit on an ellipse of radii ``ORBIT`` (fractions of w and h) around the centre,
    evenly spaced by angle, the first at the top and then clockwise. The count is
    ``MAX_SATELLITES`` (8) when ``w >= WIDE_RATIO * h`` (letter), else ``MIN_SATELLITES`` (6)
    (a5, b6), so narrow canvases keep roomier shapes. Shape radii are fractions of w and h
    chosen so no bounding boxes overlap and everything stays inside the canvas.
    """

    id = "ideas"
    added_value = 3
    name = "Idea map"
    category = "value_added"
    section = "value_added"

    MIN_SATELLITES = 6
    MAX_SATELLITES = 8
    WIDE_RATIO = 0.78
    CENTRE_RADII = (0.16, 0.10)  # fractions of (w, h)
    SAT_RADII = (0.16, 0.06)
    ORBIT = (0.33, 0.43)
    RULE_Y = 0.3  # satellite rule offset below its centre, fraction of ry
    RULE_W = 0.7  # rule half-width as a fraction of rx

    def __init__(self, count: int = 1) -> None:
        if count < 0:
            raise ValueError("count must be >= 0")
        self.count = count

    def instances(self, config: Config) -> list[Ctx]:
        return [{} for _ in range(self.count)]

    @classmethod
    def layout(cls, w: float, h: float) -> IdeaLayout:
        """Shapes for a ``w`` x ``h`` canvas, positions relative to its top-left."""
        n = cls.MAX_SATELLITES if w >= cls.WIDE_RATIO * h else cls.MIN_SATELLITES
        cx, cy = w / 2, h / 2
        sats = []
        for k in range(n):
            t = -math.pi / 2 + 2 * math.pi * k / n
            sats.append((cx + cls.ORBIT[0] * w * math.cos(t), cy + cls.ORBIT[1] * h * math.sin(t)))
        return IdeaLayout(
            (cx, cy),
            (cls.CENTRE_RADII[0] * w, cls.CENTRE_RADII[1] * h),
            (cls.SAT_RADII[0] * w, cls.SAT_RADII[1] * h),
            sats,
        )

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        pdf.c_margin = 0
        pdf.set_text_color(*color(pdf, "accent"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[3])
        h = g.header
        pdf.set_xy(h.x, h.y)
        pdf.cell(h.w, h.h, s("ideas.title"))

        c = g.content
        lay = self.layout(c.w, c.h)
        ox, oy = c.x, c.y
        cx, cy = ox + lay.centre[0], oy + lay.centre[1]
        crx, cry = lay.centre_radii
        srx, sry = lay.sat_radii

        pdf.set_draw_color(*color(pdf, "muted"))
        pdf.set_line_width(tokens.STROKE_LIGHT)
        for sx, sy in lay.satellites:
            pdf.line(cx, cy, ox + sx, oy + sy)
        pdf.set_fill_color(*color(pdf, "tint"))
        pdf.ellipse(cx - crx, cy - cry, 2 * crx, 2 * cry, style="DF")
        pdf.set_fill_color(255, 255, 255)
        for sx, sy in lay.satellites:
            pdf.ellipse(ox + sx - srx, oy + sy - sry, 2 * srx, 2 * sry, style="DF")

        pdf.set_draw_color(*color(pdf, "line"))
        pdf.set_line_width(tokens.STROKE_HAIRLINE)
        for sx, sy in lay.satellites:
            y = oy + sy + sry * self.RULE_Y
            pdf.line(ox + sx - srx * self.RULE_W, y, ox + sx + srx * self.RULE_W, y)
        y = cy + cry * self.RULE_Y
        pdf.line(cx - crx * self.RULE_W, y, cx + crx * self.RULE_W, y)
        pdf.set_text_color(*color(pdf, "muted"))
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[0])
        pdf.set_xy(cx - crx, cy - g.baseline)
        pdf.cell(2 * crx, g.baseline, s("ideas.main"), align="C")
