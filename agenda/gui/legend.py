"""Legend widget: colored swatch + label + count per section; click jumps to its first page."""

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from agenda.gui import help_text
from agenda.gui import legend_model as M
from agenda.gui import section_colors as C


class Legend(QWidget):
    """Rebuilt on every plan; `entries` holds the current LegendEntry list."""

    section_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[M.LegendEntry] = []
        self.buttons: dict[str, QPushButton] = {}
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(4, 2, 4, 2)
        self.title = QLabel("Legend:")
        self.title.setObjectName("legend_title")
        self.title.setToolTip(
            "The colors mark the agenda sections in the bar above. "
            "Hatching marks padding (blank filler pages)."
        )
        self._row.addWidget(self.title)

    def dark(self) -> bool:
        return C.is_dark(self.palette().window().color().lightness())

    def set_entries(self, entries: list[M.LegendEntry]) -> None:
        self.entries = list(entries)
        while self._row.count():
            item = self._row.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.title:
                w.deleteLater()
        self.buttons = {}
        self._row.addWidget(self.title)
        for e in self.entries:
            btn = QPushButton(f"{e.label} {e.count}")
            btn.setFlat(True)
            tip = f"{help_text.section_tooltip(e.key)}\nClick to go to the first {e.label} page."
            btn.setToolTip(tip)
            btn.clicked.connect(lambda _=False, k=e.key: self.section_clicked.emit(k))
            sw = QLabel()
            sw.setFixedSize(12, 12)
            sw.setObjectName(f"swatch_{e.key}")
            sw.setToolTip(tip)
            self._row.addWidget(sw)
            self._row.addWidget(btn)
            self.buttons[e.key] = btn
        self._row.addStretch(1)
        self.recolor()

    def recolor(self) -> None:
        """Apply section colors for the current light/dark palette (text keeps normal color)."""
        for e in self.entries:
            sw = self.findChild(QLabel, f"swatch_{e.key}")
            if sw is not None:
                sw.setStyleSheet(
                    f"background-color: {QColor(C.section_color(e.key, self.dark())).name()};"
                )

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type().name == "PaletteChange":
            self.recolor()
