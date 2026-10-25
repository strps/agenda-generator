"""Phase 5 Done-when: every optional page renders at every supported size inside the safe area."""

import io

import pytest
from helpers import assert_in_safe_area
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.catalog import get_page
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.sizes import SIZES

OPTIONAL_IDS = (
    "goals",
    "important_dates",
    "todo",
    "projects",
    "budget",
    "habits",
    "monthly_review",
    "schedule",
    "holidays",
    "passwords",
)


def _render(page_id, cfg):
    from helpers import render_page

    return render_page(get_page(page_id), cfg)


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", tuple(SIZES))
@pytest.mark.parametrize("page_id", OPTIONAL_IDS)
def test_optional_page_in_safe_area_at_every_size(page_id, size, lang):
    cfg = Config(language=lang, page_size=size)
    data = _render(page_id, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) >= 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("size", tuple(SIZES))
def test_export_with_all_optional_pages(size, tmp_path):
    cfg = Config(page_size=size, pages=list(OPTIONAL_IDS))
    plan = build_plan(cfg)
    out = export_agenda(cfg, tmp_path / "a.pdf")
    reader = PdfReader(str(out))
    assert len(reader.pages) == len(plan)
    for pid in OPTIONAL_IDS:
        assert any(e.page_class is get_page(pid) for e in plan)
