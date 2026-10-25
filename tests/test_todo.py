import io

import pytest
from helpers import assert_in_safe_area, drawn_points, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import Todo

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_todo():
    assert get_page("todo") is Todo
    assert Todo in pages_by_category("optional")
    assert (Todo.category, Todo.section, Todo.pages) == ("optional", "optional", 1)
    assert Todo().instances(Config()) == [{}]


def test_count_and_negative():
    assert len(Todo(count=3).instances(Config())) == 3
    assert Todo(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Todo(count=-1)


def test_layout_rule():
    assert Todo.layout(27) == 26
    assert Todo.layout(48) == 47
    assert Todo.layout(0) == 0


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Todo, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, title, due in (("es", "Lista de tareas", "Fecha"), ("en", "To-do list", "Due")):
        text = PdfReader(io.BytesIO(render_page(Todo, Config(language=lang)))).pages[0]
        text = text.extract_text()
        assert title in text and due in text


@pytest.mark.parametrize("size", SIZES)
def test_one_checkbox_per_row(size):
    cfg = Config(page_size=size)
    rows = Todo.layout(Grid.from_config(cfg).rows)
    pts = drawn_points(render_page(Todo, cfg))[0]
    left = min(x for x, _ in pts)
    ys = {round(y, 2) for x, y in pts if abs(x - left) < 0.01}
    # each box has a top and bottom edge at the left x (plus the label text origin)
    assert 2 * rows <= len(ys) <= 2 * rows + 2


def test_plan_includes_todo_only_when_listed():
    plan = build_plan(Config(pages=["todo"]))
    assert [e.page_class for e in plan].count(Todo) == 1
    assert Todo not in [e.page_class for e in build_plan(Config())]
