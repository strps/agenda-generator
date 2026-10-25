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
