import io
from datetime import date

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.calendar import days_in_month
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import Habits

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_habits():
    assert get_page("habits") is Habits
    assert Habits in pages_by_category("optional")
    assert (Habits.category, Habits.section, Habits.pages) == ("optional", "optional", 1)


def test_twelve_month_instances():
    ctxs = Habits().instances(Config(year=2027))
    assert [c["month"] for c in ctxs] == list(range(1, 13))
    assert {c["year"] for c in ctxs} == {2027}


def test_layout_rule():
    assert Habits.layout(0) == 0
    assert Habits.layout(Habits.HEADER_ROWS) == 0
    assert Habits.layout(Habits.HEADER_ROWS + 5) == 5
    assert Habits.layout(500) == Habits.MAX_HABITS


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    assert Habits.layout(Grid.from_config(Config(page_size=size)).rows) >= 8


def _circles_per_page(data: bytes) -> list[int]:
    out = []
    for pg in PdfReader(io.BytesIO(data)).pages:
        n = 0

        def on_op(op, args, cm, tm):
            nonlocal n
            n += op == b"c"

        pg.extract_text(visitor_operand_before=on_op)
        out.append(n // 4)  # one circle = 4 bezier curves
    return out


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area_and_circle_counts(lang, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(Habits, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 12
    assert_in_safe_area(data, cfg)
    habits = Habits.layout(Grid.from_config(cfg).rows)
    counts = _circles_per_page(data)
    assert counts == [habits * days_in_month(2027, m) for m in range(1, 13)]
    assert counts[1] == habits * 28 and counts[0] == habits * 31


def test_leap_february_has_29_columns():
    counts = _circles_per_page(render_page(Habits, Config(year=2028)))
    assert counts[1] // Habits.layout(Grid.from_config(Config()).rows) == 29
    assert date(2028, 2, 29).month == 2


def test_localized_text():
    for lang, month, title, label in (
        ("es", "Marzo", "Hábitos", "Hábito"),
        ("en", "March", "Habits", "Habit"),
    ):
        pages = PdfReader(io.BytesIO(render_page(Habits, Config(language=lang)))).pages
        text = pages[2].extract_text()
        assert title in text and label in text and month in text


def test_plan_has_twelve_habit_pages_in_month_order():
    plan = build_plan(Config(pages=["habits"]))
    entries = [e for e in plan if e.page_class is Habits]
    assert [e.ctx["month"] for e in entries] == list(range(1, 13))
    assert Habits not in [e.page_class for e in build_plan(Config())]
