import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication  # noqa: E402

from agenda.gui.collapsible import CollapsibleSection  # noqa: E402


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
