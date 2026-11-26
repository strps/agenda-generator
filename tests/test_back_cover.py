import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.pages.core import BackCover


def test_registered_as_core_front_back():
    assert get_page("back_cover") is BackCover
    assert BackCover in pages_by_category("core")
    assert (BackCover.category, BackCover.section, BackCover.pages) == ("core", "front_back", 1)


def test_single_instance():
    assert BackCover().instances(Config()) == [{}]


@pytest.mark.parametrize(
    "lang,line", [("es", "Que cada día cuente"), ("en", "Make every day count")]
)
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4"])
def test_renders_valid_pdf_in_safe_area(lang, line, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(BackCover, cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "2027" in text and line in text
    assert_in_safe_area(data, cfg)


def _plan(**kw):
    from agenda.assembler import build_plan

    return build_plan(Config(year=2026, planners=["weekly"], **kw))


def _per(cfg):
    from agenda.assembler import pages_per_booklet

    return pages_per_booklet(cfg.booklet_size, cfg.booklet_unit, cfg.booklet_folded)


def test_off_by_default():
    assert Config().back_cover is False
    plan = _plan()
    assert not any(e.page_class is BackCover for e in plan)
    assert len(plan) % _per(Config()) == 0


def test_on_is_last_page():
    assert _plan(back_cover=True)[-1].page_class is BackCover


@pytest.mark.parametrize("folded", [True, False])
def test_separate_covers_without_back_cover(folded):
    cfg = Config(year=2026, planners=["weekly"], separate_covers=True, booklet_folded=folded)
    from agenda.assembler import build_plan, summarize

    plan = build_plan(cfg)
    outside = [e for e in plan if e.booklet_index is None]
    inner = [e for e in plan if e.booklet_index is not None]
    assert len(outside) == 2 and [e.page_number for e in outside] == [1, 2]
    assert plan[-1].booklet_index is not None and plan[-1].kind != "filler"
    assert inner[0].page_number == 3 and inner[0].side == "right"
    assert len(inner) % _per(cfg) == 0
    if folded:
        assert len(inner) % 4 == 0
    assert summarize(plan, cfg).cover_pages == 2


def test_separate_covers_with_back_cover_summary():
    from agenda.assembler import build_plan, summarize

    cfg = Config(year=2026, planners=["weekly"], separate_covers=True, back_cover=True)
    plan = build_plan(cfg)
    assert len([e for e in plan if e.booklet_index is None]) == 4
    assert summarize(plan, cfg).cover_pages == 4


def test_cli_flag(tmp_path):
    from agenda import cli

    assert cli.main(["--back-cover", "--dry-run", "-o", str(tmp_path / "a.pdf")]) == 0
    assert cli.main(["--no-back-cover", "--dry-run", "-o", str(tmp_path / "a.pdf")]) == 0


def test_group_is_global():
    from agenda import templates

    assert templates.group_of("back_cover") == "global"


@pytest.mark.gui
@pytest.mark.parametrize("lang", ["en", "es"])
def test_gui_tooltip(lang):
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from agenda import uitext
    from agenda.gui.settings_panel import SettingsPanel

    QApplication.instance() or QApplication([])
    uitext.set_language(lang)
    try:
        panel = SettingsPanel()
        assert panel.editors["back_cover"].toolTip().strip()
    finally:
        uitext.set_language("en")
