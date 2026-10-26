import os
from types import SimpleNamespace as NS

import pytest

from agenda.assembler import build_plan, summarize
from agenda.config import Config
from agenda.gui import legend_model as M


def entry(section, kind="page"):
    return NS(section=section, kind=kind, booklet_index=None)


def test_entries_count_in_label_order_and_skip_absent():
    plan = [entry("weekly"), entry("front_back"), entry("weekly"), entry("x", "padding")]
    got = M.legend_entries(plan)
    assert got == [
        ("front_back", "Front/back", 1),
        ("weekly", "Weekly", 2),
        ("padding", "Padding", 1),
    ]
    assert M.legend_entries([]) == []


def test_entries_sum_to_plan_length():
    plan = build_plan(Config())
    assert sum(e.count for e in M.legend_entries(plan)) == len(plan)


def test_summary_text_matches_assembler_numbers():
    cfg = Config()
    s = summarize(build_plan(cfg), cfg)
    text = M.summary_text(s)
    assert text.startswith(f"{s.total_pages} pages · {s.total_sheets} sheets")
    assert f"{s.booklets} booklet" in text


def test_summary_text_singular_padding_and_warnings():
    s = NS(total_pages=1, total_sheets=1, booklets=1, padding_pages=1, warnings=("a", "b"))
    assert M.summary_text(s) == "1 page · 1 sheet · 1 booklet · 1 padding page · ⚠ 2 warnings"
    assert M.summary_tooltip(s) == "a\nb"
    s = NS(total_pages=4, total_sheets=1, booklets=1, padding_pages=0, warnings=())
    assert M.summary_text(s) == "4 pages · 1 sheet · 1 booklet"


def test_widget_legend_summary_click_and_error():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from agenda.gui.app import MainWindow

    win = MainWindow()
    plan = win.section_bar.plan
    assert [e.key for e in win.legend.entries] == [e.key for e in M.legend_entries(plan)]
    assert win.summary_label.text().startswith(f"{len(plan)} pages")
    key = "weekly"
    win.legend.buttons[key].click()
    from agenda.gui.bar_model import first_page_of, next_run_of
    from agenda.gui.section_colors import section_color

    first = first_page_of(plan, key)
    assert win.preview.index == first
    win.legend.buttons[key].click()
    assert win.preview.index == next_run_of(plan, key, first) > first
    assert win.legend.buttons[key].color.name() == section_color(key, win.legend.dark())
    win.preview.wait_idle()
    win.settings.editors["imposition"].setChecked(True)
    win.settings.editors["booklet_folded"].setChecked(False)
    win.update_preview()
    assert win.summary_label.text() == M.NO_PLAN_TEXT
    assert win.legend.entries == []
    win.preview.wait_idle()


def _legend_with(entries):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from agenda.gui.legend import Legend

    lg = Legend()
    lg.set_entries(entries)
    return lg


def test_legend_tooltips_explain_colors():
    from PySide6.QtWidgets import QLabel

    from agenda.gui.help_text import SECTION_DESCRIPTIONS

    lg = _legend_with(M.legend_entries(build_plan(Config())))
    assert lg.entries
    for e in lg.entries:
        tip = lg.buttons[e.key].toolTip()
        assert SECTION_DESCRIPTIONS[e.key] in tip
        assert "first" in tip and "next" in tip
    title = lg.findChild(QLabel, "legend_title")
    assert title is not None and title.toolTip()
    lg.set_entries(lg.entries)
    assert lg.findChild(QLabel, "legend_title") is not None


def test_legend_padding_description():
    from agenda.gui.help_text import SECTION_DESCRIPTIONS

    lg = _legend_with([M.LegendEntry("padding", "Padding", 2)])
    assert SECTION_DESCRIPTIONS["padding"] in lg.buttons["padding"].toolTip()


def _colors(widget):
    img = widget.grab().toImage()
    return {img.pixel(x, y) for x in range(img.width()) for y in range(img.height())}


def _corner(widget):
    """Colors of a text-free 8x8 corner of a legend chip."""
    img = widget.grab().toImage()
    return {img.pixel(x, y) for x in range(2, 10) for y in range(2, 10)}


def test_chips_fill_color_and_padding_is_hatched():
    lg = _legend_with([M.LegendEntry("padding", "Padding", 2), M.LegendEntry("monthly", "Monthly", 3)])
    lg.resize(600, 40)
    lg.show()
    assert len(_corner(lg.buttons["padding"])) >= 2
    monthly = _corner(lg.buttons["monthly"])
    assert len(monthly) == 1 and lg.buttons["monthly"].color.rgb() in monthly
    lg.recolor()
    assert len(_corner(lg.buttons["padding"])) >= 2
