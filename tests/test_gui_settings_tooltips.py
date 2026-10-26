import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, QPoint, QPointF
from PySide6.QtGui import QEnterEvent, QHelpEvent
from PySide6.QtWidgets import QApplication, QLabel, QPlainTextEdit

from agenda.config import Config
from agenda.gui.help_text import PARAM_SHORT, param_tooltip
from agenda.gui.hover_tooltip import HOVER_EXPAND_MS
from agenda.gui.settings_panel import SettingsPanel


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _enter(w):
    p = QPointF(1, 1)
    QApplication.sendEvent(w, QEnterEvent(p, p, p))


def _tip(w):
    QApplication.sendEvent(w, QHelpEvent(QEvent.Type.ToolTip, QPoint(1, 1), QPoint(1, 1)))


def test_all_params_have_tooltips(qapp):
    panel = SettingsPanel()
    names = set(Config.model_fields)
    assert set(panel.tooltips) == set(panel.editors) == names
    for n in names:
        assert panel.editors[n].toolTip() == PARAM_SHORT[n]
        assert panel.tooltips[n].expand_timer.interval() == HOVER_EXPAND_MS


def test_editor_hover_expands(qapp):
    panel = SettingsPanel()
    for n, w in panel.editors.items():
        target = w.viewport() if isinstance(w, QPlainTextEdit) else w
        tip = panel.tooltips[n]
        _enter(target)
        assert tip.expand_timer.isActive(), n
        _tip(target)
        assert tip.current_text() == param_tooltip(n), n
        tip.expand_timer.timeout.emit()
        assert tip.current_text() == param_tooltip(n, True), n
        QApplication.sendEvent(target, QEvent(QEvent.Type.Leave))
        assert tip.current_text() == ""
        assert not tip.expand_timer.isActive()


def test_labels_have_tooltips(qapp):
    panel = SettingsPanel()
    for n in Config.model_fields:
        if n in ("pages", "month_start_pages", "month_end_pages"):  # unlabeled checkbox lists
            assert n not in panel.label_tooltips
            continue
        label = panel.findChild(QLabel, f"label_{n}")
        assert label is not None and label.text() == n.replace("_", " ")
        tip = panel.label_tooltips[n]
        _enter(label)
        _tip(label)
        tip.expand_timer.timeout.emit()
        assert tip.current_text() == param_tooltip(n, True)


def test_main_window_settings_tooltips(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert set(win.settings.tooltips) == set(Config.model_fields)
