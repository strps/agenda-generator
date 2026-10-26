import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF
from PySide6.QtGui import QEnterEvent, QHelpEvent
from PySide6.QtWidgets import (
    QApplication,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
)

from agenda.gui import hover_tooltip, section_bar
from agenda.gui.hover_tooltip import ExpandingToolTip

SHORT = "short text"
DETAIL = "detailed explanation"


pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def enter(w):
    p = QPointF(1, 1)
    QApplication.sendEvent(w, QEnterEvent(p, p, p))


def tip_event(w):
    QApplication.sendEvent(w, QHelpEvent(QEvent.Type.ToolTip, QPoint(1, 1), QPoint(1, 1)))


def leave(w):
    QApplication.sendEvent(w, QEvent(QEvent.Type.Leave))


@pytest.fixture
def btn(qapp):
    b = QPushButton("x")
    return b, ExpandingToolTip(b, SHORT, DETAIL)


def test_constant_shared_and_timer(btn):
    _b, tip = btn
    assert section_bar.HOVER_EXPAND_MS is hover_tooltip.HOVER_EXPAND_MS
    assert tip.expand_timer.interval() == hover_tooltip.HOVER_EXPAND_MS
    assert tip.expand_timer.isSingleShot()


def test_enter_starts_timer_then_tooltip_shows_short(btn):
    b, tip = btn
    assert b.toolTip() == SHORT
    enter(b)
    assert tip.expand_timer.isActive() and not tip.expanded
    tip_event(b)
    assert tip.current_text() == SHORT


def test_expand_after_timeout_then_tooltip(btn):
    b, tip = btn
    enter(b)
    tip.expand_timer.timeout.emit()
    assert tip.expanded
    assert tip.current_text() == SHORT + "\n" + DETAIL
    tip_event(b)
    assert tip.current_text() == SHORT + "\n" + DETAIL


def test_repeat_events_keep_expanded_and_timer_idle(btn):
    b, tip = btn
    enter(b)
    tip.expand_timer.stop()
    tip.expand_timer.timeout.emit()
    tip_event(b)
    assert tip.current_text() == SHORT + "\n" + DETAIL
    assert not tip.expand_timer.isActive()
    enter(b)
    assert not tip.expand_timer.isActive()


def test_leave_resets(btn):
    b, tip = btn
    enter(b)
    tip.expand_timer.timeout.emit()
    leave(b)
    assert tip.current_text() == ""
    assert not tip.expand_timer.isActive()
    assert not tip.expanded
    enter(b)
    tip_event(b)
    assert tip.current_text() == SHORT


def test_tooltip_without_enter_starts_timer(btn):
    b, tip = btn
    tip_event(b)
    assert tip.expand_timer.isActive()
    assert tip.current_text() == SHORT


def test_repeated_enter_does_not_restart_timer(btn):
    b, tip = btn
    enter(b)
    tip.expand_timer.stop()
    tip.expand_timer.start()
    enter(b)
    tip_event(b)
    assert tip.expand_timer.isActive()


def test_spinbox_child_events(qapp):
    sb = QSpinBox()
    tip = ExpandingToolTip(sb, SHORT, DETAIL)
    enter(sb)
    tip.reset()
    enter(sb)
    enter(sb.lineEdit())
    assert tip.expand_timer.isActive()
    tip_event(sb.lineEdit())
    assert tip.current_text() == SHORT
    tip.expand_timer.timeout.emit()
    tip_event(sb.lineEdit())
    assert tip.current_text() == SHORT + "\n" + DETAIL


def test_plaintext_viewport_events(qapp):
    pt = QPlainTextEdit()
    tip = ExpandingToolTip(pt, SHORT, DETAIL)
    enter(pt.viewport())
    assert tip.expand_timer.isActive()
    tip_event(pt.viewport())
    assert tip.current_text() == SHORT
    tip.expand_timer.timeout.emit()
    assert tip.current_text() == SHORT + "\n" + DETAIL
    leave(pt.viewport())
    assert tip.current_text() == ""


def test_set_texts_resets(btn):
    b, tip = btn
    enter(b)
    tip.expand_timer.timeout.emit()
    tip.set_texts("s2", "d2")
    assert b.toolTip() == "s2"
    assert not tip.expanded and tip.current_text() == ""
    enter(b)
    tip.expand_timer.timeout.emit()
    assert tip.current_text() == "s2\nd2"
