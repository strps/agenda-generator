import io
from datetime import date

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.calendar import days_in_month
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.draw import MOOD_LEVELS, draw_mood
from agenda.exporter import new_document
from agenda.grid import Grid
from agenda.i18n import LANGUAGES, STRINGS
from agenda.pages.value_added import HealthTracker as HT

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_health():
    assert get_page("health") is HT
    assert HT in pages_by_category("value_added")
    assert (HT.category, HT.section, HT.pages) == ("value_added", "value_added", 1)


def test_twelve_month_instances():
    ctxs = HT().instances(Config(year=2027))
    assert [c["month"] for c in ctxs] == list(range(1, 13))


def test_layout_rule():
    assert HT.layout(0) == 0
    fixed = HT.LEGEND_ROWS + HT.GAP_ROWS + HT.DAYS_ROWS
    assert HT.layout(fixed + HT.ROW_ROWS) == 1
    assert HT.layout(fixed + 3 * HT.ROW_ROWS + 1) == 3
    assert HT.layout(500) == len(HT.TRACKERS)


@pytest.mark.parametrize("size", SIZES)
def test_all_trackers_fit_each_size(size):
    assert HT.layout(Grid.from_config(Config(page_size=size)).rows) == len(HT.TRACKERS)


def _content(draw_fn_level: int) -> bytes:
    pdf = new_document(Config())
    pdf.add_page()
    draw_mood(pdf, 20, 20, 8, draw_fn_level)
    page = PdfReader(io.BytesIO(bytes(pdf.output()))).pages[0]
    return page.get_contents().get_data()


def test_draw_mood_five_distinct_shapes():
    shapes = {_content(lv) for lv in MOOD_LEVELS}
    assert len(shapes) == 5


def test_draw_mood_rejects_bad_level():
    pdf = new_document(Config())
    pdf.add_page()
    for lv in (0, 6):
        with pytest.raises(ValueError):
            draw_mood(pdf, 10, 10, 5, lv)


def _rects_per_page(data: bytes) -> list[int]:
    out = []
    for pg in PdfReader(io.BytesIO(data)).pages:
        n = 0

        def on_op(op, args, cm, tm):
            nonlocal n
            n += op == b"re"

        pg.extract_text(visitor_operand_before=on_op)
        out.append(n)
    return out


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area_one_cell_per_day_per_row(lang, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(HT, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 12
    assert_in_safe_area(data, cfg)
    n = HT.layout(Grid.from_config(cfg).rows)
    rects = _rects_per_page(data)
    for m, count in enumerate(rects, start=1):
        days = days_in_month(2027, m)
        weekends = sum(1 for d in range(1, days + 1) if date(2027, m, d).weekday() >= 5)
        # per-day cells + exercise checkbox (one per day) + weekend tints
        assert count == days * n + days + weekends
    assert days_in_month(2027, 2) == 28 and days_in_month(2027, 1) == 31


def test_localized_text():
    for lang, month, title, label in (
        ("es", "Marzo", "Salud", "Ánimo"),
        ("en", "March", "Health", "Mood"),
    ):
        pages = PdfReader(io.BytesIO(render_page(HT, Config(language=lang)))).pages
        text = pages[2].extract_text()
        assert title in text and label in text and month in text


def test_strings_in_all_languages():
    for key in ("title", "mood", "water", "sleep", "exercise", "other"):
        for lang in LANGUAGES:
            assert STRINGS[lang][f"health.{key}"]


def test_plan_has_twelve_health_pages_when_listed():
    plan = build_plan(Config(pages=["health"]))
    entries = [e for e in plan if e.page_class is HT]
    assert [e.ctx["month"] for e in entries] == list(range(1, 13))
    assert HT not in [e.page_class for e in build_plan(Config())]
