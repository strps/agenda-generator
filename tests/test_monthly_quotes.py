import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.grid import Grid
from agenda.i18n import LANGUAGES, STRINGS
from agenda.pages.value_added import MonthlyQuotes as MQ

SIZES = ("a5", "b6", "letter")


def test_registered_as_value_added_quotes():
    assert get_page("quotes") is MQ
    assert MQ in pages_by_category("value_added")
    assert (MQ.category, MQ.section, MQ.pages) == ("value_added", "value_added", 1)


def test_twelve_month_instances():
    ctxs = MQ().instances(Config(year=2027))
    assert [c["month"] for c in ctxs] == list(range(1, 13))
    assert {c["year"] for c in ctxs} == {2027}


@pytest.mark.parametrize("lang", LANGUAGES)
def test_twelve_nonempty_quotes_per_language(lang):
    keys = sorted(k for k in STRINGS[lang] if k.startswith("quotes.") and k[7:].isdigit())
    assert keys == sorted(f"quotes.{m}" for m in range(1, 13))
    assert all(STRINGS[lang][k].strip() for k in keys)
    assert len({STRINGS[lang][k] for k in keys}) == 12


def test_layout_rule():
    assert MQ.layout(0) == (0, 0)
    for rows in range(60):
        q, rules = MQ.layout(rows)
        assert q % MQ.LINE_ROWS == 0 and rules >= 0 and q + rules <= rows


@pytest.mark.parametrize("size", SIZES)
def test_layout_has_reflection_rules(size):
    rows = Grid.from_config(Config(page_size=size)).rows
    assert MQ.layout(rows)[1] >= 3


@pytest.mark.parametrize("lang", LANGUAGES)
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(MQ, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 12
    assert_in_safe_area(data, cfg)


def test_localized_text():
    for lang, month, label in (("es", "Marzo", "reflexión"), ("en", "March", "reflection")):
        pages = PdfReader(io.BytesIO(render_page(MQ, Config(language=lang)))).pages
        text = pages[2].extract_text()
        assert month in text and label in text
        assert STRINGS[lang]["quotes.3"].split()[0] in text


def test_plan_has_twelve_quote_pages_only_when_listed():
    plan = build_plan(Config(pages=["quotes"]))
    entries = [e for e in plan if e.page_class is MQ]
    assert [e.ctx["month"] for e in entries] == list(range(1, 13))
    assert MQ not in [e.page_class for e in build_plan(Config())]
