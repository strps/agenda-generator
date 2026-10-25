import io
import os
from pathlib import Path

import pytest
from helpers import drawn_points
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.cli import main
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.gui import export_model as M

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


def test_default_path_uses_config_output_and_pdf_suffix():
    assert M.default_path(Config(output=Path("out/a.pdf"))) == "out/a.pdf"
    assert M.default_path(Config(output=Path("agenda"))) == "agenda.pdf"
    assert M.ensure_pdf("x.PDF") == Path("x.PDF")


def test_progress_fraction_clamped():
    assert M.progress_fraction(0, 0) == 0.0
    assert M.progress_fraction(5, 10) == 0.5
    assert M.progress_fraction(12, 10) == 1.0
    assert M.progress_percent(1, 3) == 33


def test_core_progress_callback_does_not_change_output(tmp_path):
    cfg = Config(**SMALL)
    calls = []
    a = export_agenda(cfg, tmp_path / "a.pdf", progress=lambda d, t: calls.append((d, t)))
    b = export_agenda(cfg, tmp_path / "b.pdf")
    n = len(build_plan(cfg))
    assert calls[-1] == (n, n) and len(calls) == n
    assert [d for d, _ in calls] == list(range(1, n + 1))
    assert a.read_bytes() == b.read_bytes() or _sig(a) == _sig(b)


def _sig(path):
    data = Path(path).read_bytes()
    texts = [p.extract_text() for p in PdfReader(io.BytesIO(data)).pages]
    return texts, drawn_points(data)


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def test_gui_export_matches_cli(qapp, tmp_path):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.settings.set_values(SMALL)
    win.flush_preview()
    assert win.export_button.isEnabled()
    gui_pdf = tmp_path / "gui.pdf"
    assert win.start_export(str(gui_pdf))
    assert not win.export_button.isEnabled()  # disabled while running
    assert not win.start_export(str(tmp_path / "again.pdf"))
    assert win.wait_export()
    assert win.export_result.startswith("Exported") and win.export_button.isEnabled()
    assert not win.export_progress.isVisible()
    cli_pdf = tmp_path / "cli.pdf"
    yaml_path = tmp_path / "c.yaml"
    assert win.save_config(str(yaml_path)) == ""
    code = main(["--config", str(yaml_path), "--output", str(cli_pdf)])
    assert code == 0
    assert _sig(gui_pdf) == _sig(cli_pdf)


def test_gui_export_error_and_invalid_config(qapp, tmp_path):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.settings.set_values(SMALL)
    win.flush_preview()
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert win.start_export(str(blocker / "sub" / "a.pdf"))  # parent is a file
    assert win.wait_export()
    assert win.export_result.startswith("Export failed")
    assert win.export_button.isEnabled()


def test_export_disabled_when_config_invalid(qapp, tmp_path):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    win.settings.set_values({**SMALL, "imposition": True, "booklet_folded": False})
    win.flush_preview()
    assert win.settings.config()[0] is None
    assert not win.export_button.isEnabled()
    assert not win.start_export(str(tmp_path / "x.pdf"))
