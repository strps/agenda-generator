import os
import subprocess
import sys

import pytest

from agenda.gui import layout as L


def test_regions_unique_and_complete():
    assert len(set(L.REGIONS)) == len(L.REGIONS)
    assert {"settings", "preview", "section_bar", "legend", "summary", "export"} <= set(L.REGIONS)


def test_splitter_sizes_sum_to_width():
    spec = L.WindowLayout()
    assert sum(spec.splitter_sizes()) == spec.width


def test_core_and_cli_import_without_pyside6():
    code = (
        "import sys; sys.modules['PySide6'] = None\n"
        "import agenda.cli, agenda.gui, agenda.gui.layout"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.mark.gui
def test_main_window_has_all_regions(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert set(win.regions) == set(L.REGIONS)
    assert win.windowTitle() == L.WindowLayout().title
    assert win.export_button.text() == "Export PDF"


@pytest.mark.gui
def test_main_window_shows_spanish_texts(qapp):
    from agenda import templates as T
    from agenda import uitext
    from agenda.gui.app import MainWindow

    uitext.set_language("es")
    win = MainWindow()
    assert win.open_button.text() == uitext.tr("app.open_config") != "Open config"
    assert win.save_button.text() == uitext.tr("app.save_config")
    assert win.export_button.text() == uitext.tr("app.export_pdf")
    assert win.menuBar().actions()[0].text() == uitext.tr("app.menu_settings")
    sec = win.settings.sections[T.MONTH_START]
    assert sec.toggle_button.text().endswith(T.section_label(T.MONTH_START))
    assert T.section_label(T.MONTH_START) != T.section(T.MONTH_START).label
    assert win.legend.title.text() == uitext.tr("legend.title")
    win.preview.wait_idle()
    win.close()


@pytest.mark.gui
def test_accepting_prefs_stores_ui_language(qapp, tmp_path, monkeypatch):
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QDialog

    from agenda import uitext
    from agenda.config import Config
    from agenda.gui import app as gui_app
    from agenda.gui.prefs_dialog import GuiSettingsDialog

    prefs = QSettings(str(tmp_path / "p.ini"), QSettings.Format.IniFormat)
    win = gui_app.MainWindow(prefs)

    def fake_exec(self):
        self.language_box.setCurrentIndex(self.language_box.findData("es"))
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(GuiSettingsDialog, "exec", fake_exec)
    before = Config().language
    win.open_preferences()
    assert prefs.value("ui_language") == "es"
    assert uitext.get_language() == "en"  # applies on restart, not live
    assert Config().language == before
    win.close()
