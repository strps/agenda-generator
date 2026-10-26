import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.gui import bar_model as B
from agenda.gui import help_text, section_bar

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def bar(qapp):
    b = section_bar.SectionBar()
    b.resize(1000, 40)
    b.set_plan(build_plan(Config()))
    return b


def _key(bar, i):
    e = bar.plan[i]
    return B.PADDING if e.kind == "padding" else e.section


def _x(bar, i):
    g = bar.geometry_for()
    return g.marker_x(i)


def _find(bar, pred, start=0):
    return next(i for i in range(start, len(bar.plan)) if pred(i))


def test_timer_config(bar):
    n = section_bar.HOVER_EXPAND_MS
    assert isinstance(n, int) and 1000 <= n <= 3000
    assert bar.expand_timer.interval() == n
    assert bar.expand_timer.isSingleShot()


def test_short_then_expanded(bar):
    i = 0
    x = _x(bar, i)
    p = bar.page_at(x)
    text = bar.hover_at(x)
    assert text == B.tooltip_text(bar.plan, p) and "\n" not in text
    assert bar.expand_timer.isActive()
    bar.expand_timer.timeout.emit()
    assert bar.current_tooltip() == text + "\n" + help_text.section_tooltip(_key(bar, p))


def test_same_section_keeps_expansion_other_restarts(bar):
    x0 = _x(bar, 0)
    p0 = bar.page_at(x0)
    bar.hover_at(x0)
    bar.expand_timer.timeout.emit()
    k = _key(bar, p0)
    j = _find(bar, lambda n: n != p0 and _key(bar, n) == k)
    p1 = bar.page_at(_x(bar, j))
    t = bar.hover_at(_x(bar, j))
    assert t == B.tooltip_text(bar.plan, p1) + "\n" + help_text.section_tooltip(k)
    d = _find(bar, lambda n: _key(bar, n) != k)
    pd = bar.page_at(_x(bar, d))
    t = bar.hover_at(_x(bar, d))
    assert t == B.tooltip_text(bar.plan, pd)
    assert bar.expand_timer.isActive()


def test_leave_resets(bar):
    x = _x(bar, 0)
    bar.hover_at(x)
    bar.expand_timer.timeout.emit()
    bar.leaveEvent(QEvent(QEvent.Type.Leave))
    assert bar.current_tooltip() == ""
    assert not bar.expand_timer.isActive()
    assert "\n" not in bar.hover_at(x)


def test_padding_expands(bar):
    try:
        i = _find(bar, lambda n: _key(bar, n) == B.PADDING)
    except StopIteration:
        pytest.skip("default plan has no padding")
    x = _x(bar, i)
    bar.hover_at(x)
    bar.expand_timer.timeout.emit()
    assert help_text.SECTION_DESCRIPTIONS[B.PADDING] in bar.current_tooltip()
