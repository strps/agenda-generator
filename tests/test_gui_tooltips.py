import os

import pytest

pytest.importorskip("PySide6")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from agenda.gui import help_text as HT  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_main_toolbar_tooltips(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert win.open_button.toolTip() == HT.TOOLTIPS["open_config"]
    assert win.save_button.toolTip() == HT.TOOLTIPS["save_config"]
    assert win.export_button.toolTip() == HT.TOOLTIPS["export_pdf"]


def test_export_tooltip_when_invalid(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.settings.set_values({"imposition": True, "booklet_folded": False})
    win.flush_preview()
    assert not win.export_button.isEnabled()
    tip = win.export_button.toolTip()
    assert HT.TOOLTIPS["export_pdf"] in tip
    assert HT.EXPORT_DISABLED_REASON in tip
