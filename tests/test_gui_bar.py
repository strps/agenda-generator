import itertools
import os
from types import SimpleNamespace as NS

import pytest

from agenda.gui import bar_model as B


def plan(spec):
    """spec: list of (section, kind, booklet) tuples."""
    return [NS(section=s, kind=k, booklet_index=b) for s, k, b in spec]


P = [
    ("front_back", "page", None),
    ("monthly", "page", 1),
    ("monthly", "page", 1),
    ("weekly", "page", 1),
    ("weekly", "page", 2),
    ("front_back", "padding", 2),
    ("front_back", "padding", 2),
    ("front_back", "page", None),
]


def test_runs_merge_and_padding_is_its_own_run():
    g = B.geometry(plan(P), 100)
    assert g.runs == [
        ("front_back", 0, 1),
        ("monthly", 1, 2),
        ("weekly", 3, 2),
        ("padding", 5, 2),
        ("front_back", 7, 1),
    ]


def test_widths_proportional_with_two_px_gaps():
    g = B.geometry(plan(P), 108)  # 4 gaps of 2 px -> 100 px for 8 pages
    assert g.page_width == 12.5
    segs = g.segments()
    assert [s.width for s in segs] == [12.5, 25, 25, 25, 12.5]
    for a, b in itertools.pairwise(segs):
        assert b.x - (a.x + a.width) == pytest.approx(2)
    assert segs[-1].x + segs[-1].width == pytest.approx(108)
    assert [s.padding for s in segs] == [False, False, False, True, False]


def test_booklet_ticks_at_first_page_of_each_booklet():
    g = B.geometry(plan(P), 108)
    assert g.booklets == (1, 4)
    assert g.ticks()[0] == pytest.approx(14.5)
    assert g.ticks()[1] == pytest.approx(g.segments()[2].x + 12.5)


def test_marker_is_page_centre_and_clamped():
    g = B.geometry(plan(P), 108)
    assert g.marker_x(0) == pytest.approx(6.25)
    assert g.marker_x(1) == pytest.approx(14.5 + 6.25)
    assert g.marker_x(99) == g.marker_x(7)
    assert g.marker_x(-3) == g.marker_x(0)


def test_marker_moves_right_monotonically():
    g = B.geometry(plan(P), 300)
    xs = [g.marker_x(i) for i in range(8)]
    assert xs == sorted(xs)


def test_empty_plan():
    g = B.geometry([], 100)
    assert g.segments() == [] and g.ticks() == [] and g.marker_x(0) == 0.0


def test_real_plan_covers_width():
    from agenda.assembler import build_plan
    from agenda.config import Config

    pl = build_plan(Config())
    g = B.geometry(pl, 1000)
    segs = g.segments()
    assert sum(s.count for s in segs) == len(pl)
    assert segs[-1].x + segs[-1].width == pytest.approx(1000)
    assert len(g.ticks()) == len({e.booklet_index for e in pl} - {None})


@pytest.mark.gui
def test_widget_follows_plan_and_marker(monkeypatch):
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.flush_preview()
    win.preview.wait_idle()
    bar = win.section_bar
    assert len(bar.plan) == len(win.preview.plan)
    win.preview.goto(5)
    win.preview.wait_idle()
    assert bar.index == win.preview.index
    assert not bar.grab().isNull()  # paints without error
    win.settings.set_values({**win.settings.values(), "num_booklets": 3})
    win.flush_preview()
    win.preview.wait_idle()
    assert len(bar.plan) == len(win.preview.plan)


# ---- interaction (task 8)

from agenda.assembler import PlanEntry


def entry(section, kind="page", booklet=None, ctx=None, n=1):
    return PlanEntry(None, ctx or {}, n, "right", booklet, section, 0, kind)


def test_page_at_clamps_and_resolves_gaps():
    g = B.geometry(plan(P), 108)  # pages 12.5 px; segments at 0, 14.5, 41.5, 68.5, 95.5
    assert g.page_at(-50) == 0 and g.page_at(0) == 0
    assert g.page_at(1000) == 7 and g.page_at(108) == 7
    assert g.page_at(14.5) == 1 and g.page_at(14.5 + 12.6) == 2
    assert g.page_at(12.9) == 0  # gap 12.5..14.5: left half -> previous page
    assert g.page_at(14.0) == 1  # right half -> next page
    assert B.geometry([], 100).page_at(5) is None


def test_page_at_inverts_marker_x():
    g = B.geometry(plan(P), 300)
    assert [g.page_at(g.marker_x(i)) for i in range(8)] == list(range(8))


def test_first_page_of_section():
    pl = plan(P)
    assert B.first_page_of(pl, "weekly") == 3
    assert B.first_page_of(pl, "padding") == 5
    assert B.first_page_of(pl, "daily") is None


def test_next_run_of_cycles_and_wraps():
    pl = plan(P)
    # front_back runs start at 0 and 7
    assert B.next_run_of(pl, "front_back", 0) == 7
    assert B.next_run_of(pl, "front_back", 3) == 7
    assert B.next_run_of(pl, "front_back", 7) == 0  # wraps
    assert B.next_run_of(pl, "weekly", 4) == 3  # single run: inside it goes back to its start
    assert B.next_run_of(pl, "weekly", 0) == 3
    assert B.next_run_of(pl, "daily", 0) is None


def test_tooltip_text():
    import datetime as dt

    days = [dt.date(2026, 3, 16) + dt.timedelta(d) for d in range(7)]
    pl = [
        entry("monthly", ctx={"month": 3}, booklet=1),
        entry("weekly", ctx={"number": 12, "days": days}, booklet=1),
        entry("daily", ctx={"date": days[0]}, booklet=1),
        entry("weekly", "padding", booklet=1),
        entry("front_back"),
    ]
    assert B.tooltip_text(pl, 0) == "Page 1 · Monthly · March · Booklet 1, sheet 1"
    assert B.tooltip_text(pl, 1) == ("Page 2 · Weekly · Week 12 (Mar 16–22) · Booklet 1, sheet 1")
    assert "Mon Mar 16" in B.tooltip_text(pl, 2)
    assert B.tooltip_text(pl, 3) == "Page 4 · Padding · Booklet 1, sheet 1"
    assert B.tooltip_text(pl, 4).startswith("Page 5 · Front/back")


def test_key_targets():
    pl = plan(P)  # booklet starts at 1 and 4
    k = lambda key, i: B.key_target(key, i, pl)
    assert k("right", 0) == 1 and k("right", 1) == 3 and k("left", 3) == 2
    assert k("left", 0) == 0 and k("right", 7) == 7
    assert k("home", 5) == 0 and k("end", 2) == 7
    assert k("pagedown", 0) == 1 and k("pagedown", 1) == 4 and k("pagedown", 5) == 7
    assert k("pageup", 5) == 4 and k("pageup", 4) == 1 and k("pageup", 1) == 0
    assert k("x", 3) == 3 and B.key_target("home", 0, []) == 0


def _window():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    QApplication.instance() or QApplication([])
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.resize(1000, 700)
    win.show()
    win.flush_preview()
    win.preview.wait_idle()
    return win


@pytest.mark.gui
def test_widget_click_drag_keys_and_legend():
    pytest.importorskip("PySide6")
    from PySide6.QtCore import QPoint, Qt
    from PySide6.QtTest import QTest

    win = _window()
    bar = win.section_bar
    geo = bar.geometry_for()
    y = 10
    x40 = int(geo.marker_x(40))
    QTest.mouseClick(bar, Qt.MouseButton.LeftButton, pos=QPoint(x40, y))
    assert bar.index == win.preview.index == geo.page_at(x40)
    # drag scrubs
    QTest.mousePress(bar, Qt.MouseButton.LeftButton, pos=QPoint(10, y))
    QTest.mouseMove(bar, QPoint(int(geo.marker_x(100)), y))
    QTest.mouseRelease(bar, Qt.MouseButton.LeftButton, pos=QPoint(int(geo.marker_x(100)), y))
    assert win.preview.index == bar.index == geo.page_at(int(geo.marker_x(100)))
    # keyboard
    QTest.keyClick(bar, Qt.Key.Key_Home)
    assert win.preview.index == 0
    QTest.keyClick(bar, Qt.Key.Key_Right)
    assert win.preview.index == B.key_target("right", 0, bar.plan)
    QTest.keyClick(bar, Qt.Key.Key_End)
    assert win.preview.index == len(bar.plan) - 1
    # legend hook and tooltip
    assert bar.first_page_of("weekly") == B.first_page_of(bar.plan, "weekly")
    assert win.preview.index == bar.index == B.first_page_of(bar.plan, "weekly")
    assert bar.first_page_of("nope") is None
    w0 = bar.index
    assert bar.next_page_of("weekly") == B.next_run_of(bar.plan, "weekly", w0) > w0
    assert win.preview.index == bar.index
    assert bar.next_page_of("nope") is None
    assert bar.tooltip_for(x40).startswith(f"Page {geo.page_at(x40) + 1} ")
    win.preview.wait_idle()
