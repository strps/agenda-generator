import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.pages.optional import Budget

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_budget():
    assert get_page("budget") is Budget
    assert Budget in pages_by_category("optional")
    assert (Budget.category, Budget.section, Budget.pages) == ("optional", "optional", 1)


def test_twelve_month_instances():
    ctxs = Budget().instances(Config(year=2027))
    assert [c["month"] for c in ctxs] == list(range(1, 13))
    assert {c["year"] for c in ctxs} == {2027}


def test_layout_rule():
    assert Budget.layout(0) == (0, 0, 0, 0)
    assert Budget.layout(Budget.FIXED_ROWS) == (0, 0, 0, 0)
    assert Budget.layout(Budget.FIXED_ROWS + 6) == (1, 2, 2, 1)
    for rows in range(80):
        counts = Budget.layout(rows)
        assert all(c >= 0 for c in counts)
        if rows >= Budget.FIXED_ROWS:
            assert Budget.FIXED_ROWS + sum(counts) == rows


@pytest.mark.parametrize("size", SIZES)
def test_layout_fits_each_size(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    assert rows >= Budget.FIXED_ROWS
    assert min(Budget.layout(rows)) >= 1


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Budget, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 12
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, month, title, label in (
        ("es", "Marzo", "Presupuesto", "Gastos fijos"),
        ("en", "March", "Budget", "Fixed expenses"),
    ):
        pages = PdfReader(io.BytesIO(render_page(Budget, Config(language=lang)))).pages
        text = pages[2].extract_text()
        assert title in text and label in text and month in text


def test_plan_has_twelve_budget_pages_in_month_order():
    plan = build_plan(Config(pages=["budget"]))
    entries = [e for e in plan if e.page_class is Budget]
    assert [e.ctx["month"] for e in entries] == list(range(1, 13))
    assert Budget not in [e.page_class for e in build_plan(Config())]
