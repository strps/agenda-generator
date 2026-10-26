import os

import pytest
from pypdf import PdfReader

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _win(tmp_path, monkeypatch):
    from PySide6.QtCore import QSettings
    from PySide6.QtWidgets import QMessageBox

    from agenda.gui.app import MainWindow

    monkeypatch.setattr(QMessageBox, "information", lambda *a, **k: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: None)
    prefs = QSettings(str(tmp_path / "prefs.ini"), QSettings.Format.IniFormat)
    win = MainWindow(prefs=prefs)
    win.settings.set_values(SMALL)
    win.flush_preview()
    return win, prefs


def _accept(monkeypatch, out, **edits):
    from agenda.gui.export_dialog import ExportDialog

    def fake_exec(self):
        for k, v in edits.items():
            if k == "layout":
                self.layout_buttons[v].click()
            elif k == "page_range":
                self.page_range_edit.setText(v)
            elif k == "open_after":
                self.open_after_box.setChecked(v)
            elif k == "page_numbers":
                self.controls["page_numbers"].setChecked(v)
        self.output_edit.setText(str(out))
        return 1

    monkeypatch.setattr(ExportDialog, "exec", fake_exec)


@pytest.mark.gui
def test_accept_applies_values_and_exports_spreads(qapp, tmp_path, monkeypatch):
    win, prefs = _win(tmp_path, monkeypatch)
    out = tmp_path / "s.pdf"
    _accept(monkeypatch, out, layout="spreads", page_numbers=True)
    win.export_dialog()
    v = win.settings.values()
    assert v["spreads"] is True and v["page_numbers"] is True
    assert win.wait_export() and win.export_result.startswith("Exported")
    page = PdfReader(str(out)).pages[0]
    assert page.mediabox.width > page.mediabox.height
    assert prefs.value("export/last_dir") == str(tmp_path)
    assert prefs.value("export/open_after", type=bool) is False


@pytest.mark.gui
def test_page_range_and_open_after(qapp, tmp_path, monkeypatch):
    win, prefs = _win(tmp_path, monkeypatch)
    opened = []
    monkeypatch.setattr(type(win), "open_file", lambda self, p: opened.append(p))
    out = tmp_path / "r.pdf"
    _accept(monkeypatch, out, page_range="2-3", open_after=True)
    win.export_dialog()
    assert win.wait_export()
    assert len(PdfReader(str(out)).pages) == 2
    assert opened == [str(out)]
    assert prefs.value("export/open_after", type=bool) is True


@pytest.mark.gui
def test_cancel_starts_no_export(qapp, tmp_path, monkeypatch):
    from agenda.gui.export_dialog import ExportDialog

    win, _prefs = _win(tmp_path, monkeypatch)
    monkeypatch.setattr(ExportDialog, "exec", lambda self: 0)
    win.export_dialog()
    assert not win.export_running


@pytest.mark.gui
def test_export_editors_hidden_but_round_trip(qapp, tmp_path, monkeypatch):
    win, _ = _win(tmp_path, monkeypatch)
    win.settings.set_values({**SMALL, "page_number_start": 5, "crop_marks": False})
    assert win.settings.values()["page_number_start"] == 5
    win.show()
    assert not win.settings.editors["page_number_start"].isVisible()
