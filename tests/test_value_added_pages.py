"""Phase 6 Done-when: every value-added page renders at every supported size inside the safe
area, and presets export valid PDFs."""

import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import all_pages, get_page
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.sizes import SIZES

VALUE_ADDED_IDS = tuple(p.id for p in all_pages() if p.category == "value_added")
URLS = ["https://example.org/a", "https://example.org/b/long/path?x=1", "plain text", "x.org"]


def test_all_value_added_pages_covered():
    assert len(VALUE_ADDED_IDS) == 14


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", tuple(SIZES))
@pytest.mark.parametrize("page_id", VALUE_ADDED_IDS)
def test_value_added_page_in_safe_area(page_id, size, lang):
    cfg = Config(language=lang, page_size=size, qr_urls=URLS)
    data = render_page(get_page(page_id), cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) >= 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("size", ("half_letter", "b6"))
def test_export_premium_preset(size, tmp_path):
    cfg = Config(page_size=size, preset="premium", qr_urls=URLS)
    plan = build_plan(cfg)
    out = export_agenda(cfg, tmp_path / "a.pdf")
    assert len(PdfReader(str(out)).pages) == len(plan)
    for pid in VALUE_ADDED_IDS:
        assert any(e.page_class is get_page(pid) for e in plan)
