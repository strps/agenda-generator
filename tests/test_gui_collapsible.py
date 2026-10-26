import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QElapsedTimer  # noqa: E402
from PySide6.QtWidgets import QApplication, QLineEdit  # noqa: E402

from agenda.gui.collapsible import ANIM_MS, CollapsibleSection  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_expand_and_enable(qapp):
    s = CollapsibleSection("x", "Title", "page")
    s.show()
    got, en = [], []
    s.expanded_changed.connect(got.append)
    s.enable_toggled.connect(en.append)
    assert not s.body.isVisibleTo(s)
    s.set_expanded(True)
    assert s.body.isVisibleTo(s) and got == [True] and s.is_expanded()
    s.enable_box.setChecked(False)
    assert en == [False] and not s.body.isEnabled() and not s.enabled_state()
    s.set_enabled_state(True)
    assert s.body.isEnabled() and en == [False] and s.enabled_state()


def test_no_box_for_none(qapp):
    assert CollapsibleSection("x", "T", "none").enable_box is None


def _settle(qapp):
    t = QElapsedTimer()
    t.start()
    while t.elapsed() < ANIM_MS * 3:
        qapp.processEvents()


def test_click_slides(qapp):
    s = CollapsibleSection("x", "Title")
    for _ in range(4):
        s.form.addRow("f", QLineEdit())
    s.show()
    s.toggle_button.click()
    assert s.is_expanded() and s.body.isVisibleTo(s)
    _settle(qapp)
    assert s.body.isVisibleTo(s) and s._clip.height() == s._clip.natural_height() > 0
    s.toggle_button.click()
    assert not s.is_expanded() and s.body.isVisibleTo(s)  # still sliding shut
    _settle(qapp)
    assert not s.body.isVisibleTo(s)
