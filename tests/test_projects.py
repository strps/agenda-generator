import io

import pytest
from helpers import assert_in_safe_area, drawn_points, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import Projects

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_projects():
    assert get_page("projects") is Projects
    assert Projects in pages_by_category("optional")
    assert (Projects.category, Projects.section, Projects.pages) == ("optional", "optional", 1)
    assert Projects().instances(Config()) == [{}]


def test_count_and_negative():
    assert len(Projects(count=3).instances(Config())) == 3
    assert Projects(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Projects(count=-1)


def test_layout_rule():
    assert Projects.layout(27) == (14, 6)
    assert Projects.layout(48) == (28, 13)
    assert Projects.layout(8) == (0, 1)
    assert Projects.layout(0) == (0, 0)
    for rows in range(60):
        t, n = Projects.layout(rows)
        assert t >= 0 and n >= 0
        assert rows < Projects.FIXED_ROWS or Projects.FIXED_ROWS + t + n == rows


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Projects, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, title, label in (
        ("es", "Planificador de proyecto", "Objetivo"),
        ("en", "Project planner", "Objective"),
    ):
        page = PdfReader(io.BytesIO(render_page(Projects, Config(language=lang)))).pages[0]
        text = page.extract_text()
        assert title in text and label in text


@pytest.mark.parametrize("size", SIZES)
def test_one_checkbox_per_task_row(size):
    cfg = Config(page_size=size)
    tasks = Projects.layout(Grid.from_config(cfg).rows)[0]
    pts = drawn_points(render_page(Projects, cfg))[0]
    left = min(x for x, _ in pts)
    ys = {round(y, 2) for x, y in pts if abs(x - left - Projects.BOX) < 0.01}
    assert len(ys) == 2 * tasks  # top and bottom edge of each box


def test_plan_includes_projects_only_when_listed():
    plan = build_plan(Config(pages=["projects"]))
    assert [e.page_class for e in plan].count(Projects) == 1
    assert Projects not in [e.page_class for e in build_plan(Config())]
