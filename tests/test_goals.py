import io

import pytest
from helpers import assert_in_safe_area, drawn_points, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.core import Daily, Notes
from agenda.pages.optional import Goals

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_goals():
    assert get_page("goals") is Goals
    assert Goals in pages_by_category("optional")
    assert (Goals.category, Goals.section, Goals.pages) == ("optional", "optional", 1)
    assert Goals().instances(Config()) == [{}]


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_rows(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    goals, steps = Goals.layout(rows)
    assert goals in (5, 6) and steps >= 1
    assert goals * (steps + 3) <= rows + 1  # last block needs no spacing row


def test_layout_fewer_steps_when_small():
    assert Goals.layout(60) == (6, 4)
    assert Goals.layout(30) == (6, 2)
    assert Goals.layout(27) == (5, 2)
    assert Goals.layout(10)[1] == 0 or Goals.layout(10)[0] == 5


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Goals, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, title, dl in (
        ("es", "Metas del año", "Fecha límite"),
        ("en", "Yearly goals", "Deadline"),
    ):
        text = (
            PdfReader(io.BytesIO(render_page(Goals, Config(language=lang)))).pages[0].extract_text()
        )
        assert title in text and dl in text


@pytest.mark.parametrize("size", SIZES)
def test_checkbox_per_step(size):
    cfg = Config(page_size=size)
    goals, steps = Goals.layout(Grid.from_config(cfg).rows)
    data = render_page(Goals, cfg)
    pts = drawn_points(data)[0]
    # each checkbox rect contributes 4 corners; count distinct x-aligned left-edge corners
    left = min(x for x, _ in pts)
    boxes = {round(y, 2) for x, y in pts if abs(x - left) < 0.01}
    assert len(boxes) >= 2 * goals * steps  # top and bottom edge per box (plus rule starts)


def test_plan_places_goals_in_optional_group_only_when_listed():
    plan = build_plan(Config(pages=["goals"]))
    entries = [e for e in plan if e.page_class is Goals]
    assert len(entries) == 1 and entries[0].section == "optional"
    idx = [e.page_class for e in plan if e.kind != "padding"]
    g = idx.index(Goals)
    assert idx[g - 1] is Daily and idx[g + 1] is Notes
    assert Goals not in [e.page_class for e in build_plan(Config())]
