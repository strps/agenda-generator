import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication, QComboBox, QDialog

from agenda.gui import style_model as S
from agenda.gui.app import MainWindow, apply_style
from agenda.gui.prefs_dialog import GuiSettingsDialog
from agenda.gui.section_colors import section_color

pytestmark = pytest.mark.gui


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
    assert win.export_button.objectName() == "export_button"


def test_appearance_changes_and_persists(qapp, tmp_path, monkeypatch):
    p = prefs(tmp_path)
    win = MainWindow(prefs=p)
    before = win.settings.values()

    def accept_light(self):
        self.appearance_box.setCurrentText("light")
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(GuiSettingsDialog, "exec", accept_light)
    win.open_preferences()
    assert win.appearance == "light"
    assert qapp.styleSheet() == S.stylesheet(False)
    assert p.value("appearance") == "light"
    assert win.settings.values() == before
    assert "appearance" not in win.settings.editors
    assert MainWindow(prefs=prefs(tmp_path)).appearance == "light"


def test_cancel_changes_nothing(qapp, tmp_path, monkeypatch):
    p = prefs(tmp_path)
    win = MainWindow(prefs=p)

    def reject(self):
        self.appearance_box.setCurrentText("light")
        return QDialog.DialogCode.Rejected

    monkeypatch.setattr(GuiSettingsDialog, "exec", reject)
    win.open_preferences()
    assert win.appearance == "dark"
    assert not p.contains("appearance")


def test_settings_menu_and_panel(qapp, tmp_path):
    win = MainWindow(prefs=prefs(tmp_path))
    menus = [a for a in win.menuBar().actions() if a.menu()]
    settings = [a.menu() for a in menus if a.text().replace("&", "") == "Settings"]
    assert settings
    assert "action_preferences" in [a.objectName() for a in settings[0].actions()]
    assert not hasattr(win.settings, "appearance_box")
    assert not [w for w in win.settings.findChildren(QComboBox) if w.objectName() == "appearance"]


def test_dialog_widgets(qapp):
    dlg = GuiSettingsDialog(appearance="dark")
    assert [dlg.appearance_box.itemText(i) for i in range(dlg.appearance_box.count())] == list(
        S.APPEARANCES
    )
    assert dlg.appearance_box.objectName() == "appearance"
    assert dlg.appearance_box.toolTip()
    dlg.appearance_box.setCurrentText("system")
    assert dlg.appearance() == "system"


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
    chip = win.legend.buttons["monthly"]
    img = chip.grab().toImage()
    assert img.pixelColor(3, 3).name() == section_color("monthly", True)
