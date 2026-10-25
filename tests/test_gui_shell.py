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


def test_main_window_has_all_regions(qapp):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert set(win.regions) == set(L.REGIONS)
    assert win.windowTitle() == L.WindowLayout().title
    assert win.export_button.text() == "Export PDF"
