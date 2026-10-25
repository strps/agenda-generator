import io

import pytest
from helpers import assert_in_safe_area, drawn_points, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.pages.core import Notes

PATTERNS = ("lined", "dotted", "grid", "blank")
SIZES = ("a5", "b6", "letter")


def test_registered_as_core_notes():
    assert get_page("notes") is Notes
    assert Notes in pages_by_category("core")
    assert (Notes.section, Notes.pages) == ("front_back", 1)


def test_instance_count():
    cfg = Config()
    assert len(Notes().instances(cfg)) == 1
    assert len(Notes(count=7).instances(cfg)) == 7
    assert Notes(count=0).instances(cfg) == []
    with pytest.raises(ValueError):
        Notes(count=-1)


@pytest.mark.parametrize("pattern", PATTERNS)
@pytest.mark.parametrize("size", SIZES)
def test_pattern_renders_inside_safe_area(pattern, size):
    cfg = Config(notes_pattern=pattern, page_size=size)
    data = render_page(Notes, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_blank_draws_only_header():
    cfg = Config(notes_pattern="blank")
    (pts,) = drawn_points(render_page(Notes, cfg))
    assert len(pts) == 1  # the header text origin only


@pytest.mark.parametrize("pattern", ("lined", "dotted", "grid"))
def test_patterns_draw_more_than_blank(pattern):
    n = len(drawn_points(render_page(Notes, Config(notes_pattern=pattern)))[0])
    assert n > 10
