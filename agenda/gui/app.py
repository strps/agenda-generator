"""Main window shell and entry point. Regions are empty placeholders filled by later tasks."""

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from agenda.assembler import build_plan
from agenda.configfile import ConfigFileError
from agenda.gui import layout as L
from agenda.gui.preview import PreviewWidget
from agenda.gui.render_cache import Debounce
from agenda.gui.section_bar import SectionBar
from agenda.gui.settings_panel import SettingsPanel

DEBOUNCE_S = 0.3  # settings edits settle this long before the preview re-renders


class MainWindow(QMainWindow):
    """Window shell. `regions` maps each name in `layout.REGIONS` to its container widget."""

    def __init__(self) -> None:
        super().__init__()
        spec = L.WindowLayout()
        self.setWindowTitle(spec.title)
        self.resize(spec.width, spec.height)
        self.setMinimumSize(spec.min_width, spec.min_height)

        self.regions: dict[str, QWidget] = {}
        root = QWidget()
        col = QVBoxLayout(root)
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)

        # Top toolbar: open/save on the left, export on the right.
        toolbar = self._region(L.TOOLBAR)
        row = QHBoxLayout(toolbar)
        self.open_button = QPushButton("Open config")
        self.save_button = QPushButton("Save config")
        row.addWidget(self.open_button)
        row.addWidget(self.save_button)
        row.addStretch(1)
        export = self._region(L.EXPORT)
        erow = QHBoxLayout(export)
        erow.setContentsMargins(0, 0, 0, 0)
        self.export_button = QPushButton("Export PDF")
        erow.addWidget(self.export_button)
        row.addWidget(export)
        col.addWidget(toolbar)

        # Middle: settings (left) | preview (center).
        split = QSplitter(Qt.Orientation.Horizontal)
        self.settings = SettingsPanel()
        self.regions[L.SETTINGS] = self.settings
        split.addWidget(self.settings)
        self.preview = PreviewWidget()
        self.regions[L.PREVIEW] = self.preview
        split.addWidget(self.preview)
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes(list(spec.splitter_sizes()))
        col.addWidget(split, 1)

        # Bottom: section bar, legend, summary.
        self.section_bar = SectionBar()
        self.regions[L.SECTION_BAR] = self.section_bar
        col.addWidget(self.section_bar)
        col.addWidget(self._placeholder(L.LEGEND, "Legend", height=24))
        col.addWidget(self._placeholder(L.SUMMARY, "Summary", height=24))
        self.setCentralWidget(root)
        self.debounce = Debounce(DEBOUNCE_S)
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(int(DEBOUNCE_S * 1000))
        self._timer.timeout.connect(self.update_preview)
        self.settings.changed.connect(self._on_settings_changed)
        self.preview.page_changed.connect(self.section_bar.set_position)
        self.update_preview()
        self.open_button.clicked.connect(self.open_config_dialog)
        self.save_button.clicked.connect(self.save_config_dialog)

    def _on_settings_changed(self) -> None:
        self.debounce.push()
        self._timer.start()

    def flush_preview(self) -> None:
        """Apply a pending settings change now (skips the debounce wait)."""
        if self.debounce.pending:
            self.update_preview()

    def update_preview(self) -> None:
        """Rebuild the plan from the current settings; pages render in the worker thread."""
        self._timer.stop()
        self.debounce.flush()
        cfg, msg = self.settings.config()
        if cfg is None:
            self.preview.set_error(msg)
            return
        plan = build_plan(cfg)
        self.section_bar.set_plan(plan)
        self.preview.set_plan(cfg, plan)
        self.section_bar.set_position(self.preview.index)

    def load_config(self, path: str) -> str:
        """Load a YAML file into the settings panel. Returns "" or the error message."""
        try:
            self.settings.load_file(path)
        except ConfigFileError as exc:
            return str(exc)
        return ""

    def save_config(self, path: str) -> str:
        """Save the settings as YAML. Returns "" or the error message."""
        return self.settings.save_file(path)

    def open_config_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open config", "", "YAML (*.yaml *.yml)")
        if path and (err := self.load_config(path)):
            QMessageBox.warning(self, "Open config", err)

    def save_config_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save config", "config.yaml", "YAML (*.yaml)")
        if path and (err := self.save_config(path)):
            QMessageBox.warning(self, "Save config", err)

    def _region(self, name: str) -> QWidget:
        w = QWidget()
        w.setObjectName(name)
        self.regions[name] = w
        return w

    def _placeholder(self, name: str, text: str, height: int | None = None) -> QWidget:
        frame = QFrame()
        frame.setObjectName(name)
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.addWidget(QLabel(text), alignment=Qt.AlignmentFlag.AlignCenter)
        if height is not None:
            frame.setFixedHeight(height)
        self.regions[name] = frame
        return frame


def main(argv: list[str] | None = None) -> int:
    """Entry point for `agenda-gui` and `python -m agenda.gui`."""
    app = QApplication.instance() or QApplication(sys.argv if argv is None else argv)
    win = MainWindow()
    win.show()
    return app.exec()
