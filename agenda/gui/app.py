"""Main window shell and entry point. Regions are empty placeholders filled by later tasks."""

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from agenda.gui import layout as L


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
        split.addWidget(self._placeholder(L.SETTINGS, "Settings"))
        split.addWidget(self._placeholder(L.PREVIEW, "Preview"))
        split.setStretchFactor(0, 0)
        split.setStretchFactor(1, 1)
        split.setSizes(list(spec.splitter_sizes()))
        col.addWidget(split, 1)

        # Bottom: section bar, legend, summary.
        col.addWidget(self._placeholder(L.SECTION_BAR, "Section bar", height=40))
        col.addWidget(self._placeholder(L.LEGEND, "Legend", height=24))
        col.addWidget(self._placeholder(L.SUMMARY, "Summary", height=24))
        self.setCentralWidget(root)

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
