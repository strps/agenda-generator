import io
import math

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.value_added import IdeaMap

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_ideas():
    assert get_page("ideas") is IdeaMap
    assert IdeaMap in pages_by_category("value_added")
    assert (IdeaMap.category, IdeaMap.section) == ("value_added", "value_added")
    assert IdeaMap.pages == 1


def test_instance_count():
    assert len(IdeaMap().instances(Config())) == 1
    assert len(IdeaMap(count=3).instances(Config())) == 3
    assert IdeaMap(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        IdeaMap(count=-1)


def _boxes(lay):
    cx, cy = lay.centre
    out = [(cx, cy, *lay.centre_radii)]
    out += [(x, y, *lay.sat_radii) for x, y in lay.satellites]
    return out


@pytest.mark.parametrize("size", SIZES)
def test_layout_inside_no_overlap_even_angles(size):
    c = Grid.from_config(Config(page_size=size)).content
    lay = IdeaMap.layout(c.w, c.h)
    boxes = _boxes(lay)
    for x, y, rx, ry in boxes:
        assert x - rx >= 0 and x + rx <= c.w
        assert y - ry >= 0 and y + ry <= c.h
    for i, a in enumerate(boxes):
        for b in boxes[i + 1 :]:
            assert abs(a[0] - b[0]) >= a[2] + b[2] or abs(a[1] - b[1]) >= a[3] + b[3]
    n = len(lay.satellites)
    assert n in (IdeaMap.MIN_SATELLITES, IdeaMap.MAX_SATELLITES)
    cx, cy = lay.centre
    ang = [
        math.atan2((y - cy) / IdeaMap.ORBIT[1] / c.h, (x - cx) / IdeaMap.ORBIT[0] / c.w)
        for x, y in lay.satellites
    ]
    for k in range(n):
        d = (ang[(k + 1) % n] - ang[k]) % (2 * math.pi)
        assert d == pytest.approx(2 * math.pi / n)
    assert ang[0] == pytest.approx(-math.pi / 2)


def test_satellite_count_rule():
    assert len(IdeaMap.layout(100, 135).satellites) == 6
    assert len(IdeaMap.layout(190, 240).satellites) == 8


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(IdeaMap, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize(
    ("lang", "words"),
    (("es", ("Mapa de ideas", "Idea principal")), ("en", ("Idea map", "Main idea"))),
)
def test_localized_text(lang, words):
    text = (
        PdfReader(io.BytesIO(render_page(IdeaMap, Config(language=lang)))).pages[0].extract_text()
    )
    for w in words:
        assert w in text


def test_plan_includes_ideas_only_when_listed():
    plan = build_plan(Config(pages=["ideas"]))
    assert [e.page_class for e in plan].count(IdeaMap) == 1
    assert IdeaMap not in [e.page_class for e in build_plan(Config())]
