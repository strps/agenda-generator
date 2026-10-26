import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QLabel

from agenda.gui import style_model as S
from agenda.gui.app import MainWindow, apply_style
from agenda.gui.section_colors import section_color
from agenda.templates import STYLING


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def reset(qapp):
    pal = qapp.palette()
    yield
    qapp.setStyleSheet("")
    qapp.setPalette(pal)


def prefs(tmp_path):
    return QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)


def test_apply_style_default_dark(qapp):
    apply_style(qapp)
    assert qapp.styleSheet() == S.stylesheet(True)
    assert qapp.palette().color(qapp.palette().ColorRole.Window).lightness() < 128


def test_window_default_dark_and_names(qapp, tmp_path):
    win = MainWindow(prefs=prefs(tmp_path))
    assert win.appearance == "dark"
    assert win.settings.appearance_box.currentText() == "dark"
    assert win.export_button.objectName() == "export_button"


def test_appearance_box_changes_and_persists(qapp, tmp_path):
    p = prefs(tmp_path)
    win = MainWindow(prefs=p)
    box = win.settings.appearance_box
    assert win.settings.sections[STYLING].isAncestorOf(box)
    before = win.settings.config()[0]
    box.setCurrentText("light")
    assert qapp.styleSheet() == S.stylesheet(False)
    assert p.value("appearance") == "light"
    assert "appearance" not in win.settings.values()
    assert "appearance" not in win.settings.editors
    assert win.settings.config()[0] == before
    win2 = MainWindow(prefs=prefs(tmp_path))
    assert win2.appearance == "light"
    assert win2.settings.appearance_box.currentText() == "light"


def test_no_write_without_user_change(qapp, tmp_path):
    p = prefs(tmp_path)
    MainWindow(prefs=p)
    assert not p.contains("appearance")


def test_spacing(qapp, tmp_path):
    win = MainWindow(prefs=prefs(tmp_path))
    for sec in win.settings.sections.values():
        m = sec.form.contentsMargins()
        assert sec.form.spacing() >= 8
        assert min(m.left(), m.right(), m.bottom()) >= 12


def test_swatch_unchanged_in_dark(qapp, tmp_path):
    apply_style(qapp)
    win = MainWindow(prefs=prefs(tmp_path))
    win.show()
    swatch = win.legend.findChild(QLabel, "swatch_monthly")
    assert swatch is not None
    img = swatch.grab().toImage()
    colors = {img.pixelColor(x, y).name() for x in range(img.width()) for y in range(img.height())}
    assert colors == {section_color("monthly", True)}
