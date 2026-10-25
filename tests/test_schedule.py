import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import weekday_names
from agenda.pages.optional import Schedule

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_schedule():
    assert get_page("schedule") is Schedule
    assert Schedule in pages_by_category("optional")
    assert (Schedule.category, Schedule.section, Schedule.pages) == ("optional", "optional", 1)
    assert len(Schedule().instances(Config())) == 1


def test_layout_rule():
    assert Schedule.layout(48) == (15, 3)  # 47 // 3 = 15 hours
    assert Schedule.layout(34) == (11, 3)
    assert Schedule.layout(27) == (13, 2)  # 3-row bands would leave 8 hours
    assert Schedule.layout(12) == (11, 1)
    assert Schedule.layout(0) == (0, 1)
    assert Schedule.layout(500)[0] == Schedule.MAX_HOURS


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    hours, rh = Schedule.layout(Grid.from_config(Config(page_size=size)).rows)
    assert hours >= Schedule.MIN_HOURS
    assert 1 + hours * rh <= Grid.from_config(Config(page_size=size)).rows


@pytest.mark.parametrize("week_start", ("monday", "sunday"))
@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size, week_start):
    cfg = Config(language=lang, page_size=size, week_start=week_start)
    data = render_page(Schedule, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("week_start", ("monday", "sunday"))
@pytest.mark.parametrize(("lang", "title"), (("es", "Horario semanal"), ("en", "Weekly schedule")))
def test_localized_text_and_day_order(lang, title, week_start):
    cfg = Config(language=lang, week_start=week_start)
    text = PdfReader(io.BytesIO(render_page(Schedule, cfg))).pages[0].extract_text()
    assert title in text and "7:00" in text
    names = weekday_names(lang, week_start, "short")
    positions = [text.index(n) for n in names]
    assert positions == sorted(positions)


def test_plan_includes_schedule_only_when_listed():
    plan = build_plan(Config(pages=["schedule"]))
    assert [e.page_class for e in plan].count(Schedule) == 1
    assert Schedule not in [e.page_class for e in build_plan(Config())]
