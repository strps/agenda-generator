import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import MonthlyReview as MR

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_monthly_review():
    assert get_page("monthly_review") is MR
    assert MR in pages_by_category("optional")
    assert (MR.category, MR.section, MR.pages) == ("optional", "optional", 1)


def test_twelve_month_instances():
    ctxs = MR().instances(Config(year=2027))
    assert [c["month"] for c in ctxs] == list(range(1, 13))
    assert {c["year"] for c in ctxs} == {2027}


def test_layout_rule():
    assert MR.layout(0) == (0, 0, 0, 0)
    assert MR.layout(MR.FIXED_ROWS) == (0, 0, 0, 0)
    assert MR.layout(MR.FIXED_ROWS + 4) == (1, 1, 1, 1)
    assert MR.layout(MR.FIXED_ROWS + 6) == (2, 2, 1, 1)
    for rows in range(60):
        assert sum(MR.layout(rows)) + MR.FIXED_ROWS <= max(rows, MR.FIXED_ROWS)


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    assert min(MR.layout(rows)) >= 2
    assert sum(MR.layout(rows)) + MR.FIXED_ROWS <= rows


def _circles(data: bytes) -> list[int]:
    out = []
    for pg in PdfReader(io.BytesIO(data)).pages:
        n = 0

        def on_op(op, args, cm, tm):
            nonlocal n
            n += op == b"c"

        pg.extract_text(visitor_operand_before=on_op)
        out.append(n // 4)
    return out


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area_with_five_circles(lang, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(MR, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 12
    assert_in_safe_area(data, cfg)
    assert _circles(data) == [5] * 12


def test_localized_text():
    for lang, month, title in (("es", "Marzo", "Revisión"), ("en", "March", "Review")):
        pages = PdfReader(io.BytesIO(render_page(MR, Config(language=lang)))).pages
        text = pages[2].extract_text()
        assert title in text and month in text


def test_plan_has_twelve_review_pages_in_month_order():
    plan = build_plan(Config(pages=["monthly_review"]))
    entries = [e for e in plan if e.page_class is MR]
    assert [e.ctx["month"] for e in entries] == list(range(1, 13))
    assert MR not in [e.page_class for e in build_plan(Config())]
