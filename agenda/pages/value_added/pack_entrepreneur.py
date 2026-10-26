"""Entrepreneur niche pack page."""

from __future__ import annotations

from typing import NamedTuple

from fpdf import FPDF

from agenda import tokens
from agenda.catalog import register
from agenda.config import Config
from agenda.draw import (
    color,
    draw_label_rule,
    font,
)
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.base import Ctx
from agenda.pages.value_added._common import _Counted


class EntrepreneurLayout(NamedTuple):
    metric_rows: int  # height of each big metric write-in box, in baselines
    pipeline_rows: int  # rule rows under the pipeline column headings
    decision_rows: int  # rule rows under "Decisions & lessons"


@register
class PackEntrepreneur(_Counted):
    """Entrepreneur weekly dashboard, ``count`` pages (default 1; id ``niche_entrepreneur``).

    The catalog lists the niche pages as ``niche_*`` (value score 5), so the three packs are
    ``niche_entrepreneur``, ``niche_student`` and ``niche_fitness``. Top to bottom: goal of the
    week (label + rule), 3 key metrics (label + big write-in box each, 2 columns wide), the
    pipeline (leads / in progress / closed, one column of rules each) and decisions & lessons.

    Fit rule (``layout(rows)``): ``FIXED_ROWS`` are structure (goal, metric label, pipeline
    title + headings, decisions label, 3 gaps); the free rows give the metric boxes
    ``free // METRIC_DIV`` rows clamped to 1..``METRIC_MAX``, the rest is split
    ``PIPELINE_SHARE`` (rounded down) to the pipeline and the remainder to decisions.
    """

    id = "niche_entrepreneur"
    added_value = 5
    name = "Entrepreneur pack"
    FIXED_ROWS = 9
    METRIC_DIV = 6
    METRIC_MAX = 4
    PIPELINE_SHARE = 0.6
    STAGES = ("leads", "progress", "closed")

    @classmethod
    def layout(cls, rows: int) -> EntrepreneurLayout:
        free = max(0, rows - cls.FIXED_ROWS)
        metric = max(1, min(cls.METRIC_MAX, free // cls.METRIC_DIV))
        rest = max(0, free - metric)
        pipe = int(rest * cls.PIPELINE_SHARE)
        return EntrepreneurLayout(metric, pipe, rest - pipe)

    def draw(self, pdf: FPDF, ctx: Ctx, config: Config, grids: list[Grid]) -> None:
        g = grids[0]
        s = Strings(config.language)
        self._header(pdf, g, s("entre.title"))
        x, w = g.safe.x, g.safe.w
        metric, pipe, dec = self.layout(g.rows)
        pdf.set_font(font(pdf, "primary"), "B", tokens.TYPE_SIZES_PT[1])
        goal = s("entre.goal")
        draw_label_rule(pdf, x, w, g.row(1), goal, pdf.get_string_width(goal) + g.gutter)

        row = 3
        span = g.columns // 3
        for i in range(3):
            cx, cw = g.col(i * span, span)
            self._label(pdf, g, cx, cw, row, f"{s('entre.metric')} {i + 1}")
            pdf.set_draw_color(*color(pdf, "line"))
            pdf.set_line_width(tokens.STROKE_LIGHT)
            pdf.rect(
                cx, g.row(row + 1) + g.baseline * 0.2, cw - g.gutter, (metric - 0.4) * g.baseline
            )
        row += metric + 2

        self._label(pdf, g, x, w, row, s("entre.pipeline"))
        for i, key in enumerate(self.STAGES):
            cx, cw = g.col(i * span, span)
            self._label(pdf, g, cx, cw, row + 1, s(f"entre.{key}"))
            self._rules(pdf, g, cx, cw - g.gutter, row + 3, max(0, pipe - 1))
        row += pipe + 3

        self._label(pdf, g, x, w, row, s("entre.decisions"))
        self._rules(pdf, g, x, w, row + 2, max(0, dec - 1))
