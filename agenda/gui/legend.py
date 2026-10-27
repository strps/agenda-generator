"""Legend widget: one full-width colored chip (label + count) per section, like a labeled bar.
Each click jumps to the next run of that section, wrapping to the first."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QWidget

from agenda.gui import help_text
from agenda.gui import legend_model as M
from agenda.gui import section_colors as C
from agenda.gui.bar_model import PADDING
from agenda.gui.style_model import SPACING
from agenda.uitext import tr

CHIP_H = 24
HATCH_ALPHA = 110  # padding hatch over the gray, light enough to keep the label readable


class LegendChip(QPushButton):
    """Paints itself (immune to the app stylesheet): section color fill, contrasting label,
    the padding hatch, and a highlight outline on hover/focus."""

    def __init__(self, entry: M.LegendEntry) -> None:
        super().__init__(f"{entry.label} {entry.count}")
        self.key = entry.key
        self.color = QColor(C.GRAY)
        self.setObjectName(f"legend_{entry.key}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(CHIP_H)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_color(self, color: QColor) -> None:
        self.color = color
        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        r = self.rect()
        fill = self.color.darker(115) if self.isDown() else self.color
        p.fillRect(r, fill)
        if self.key == PADDING:
            hatch = QColor(self.palette().window().color())
            hatch.setAlpha(HATCH_ALPHA)
            p.fillRect(r, QBrush(hatch, Qt.BrushStyle.BDiagPattern))
        p.setPen(QColor(C.text_on(fill.name())))
        p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.text())
        if self.underMouse() or self.hasFocus():
            p.setPen(QPen(self.palette().highlight().color(), 2))
            p.drawRect(r.adjusted(1, 1, -1, -1))
        p.end()


class Legend(QWidget):
    """Rebuilt on every plan; `entries` holds the current LegendEntry list."""

    section_clicked = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[M.LegendEntry] = []
        self.buttons: dict[str, LegendChip] = {}
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(SPACING["margin"], 2, SPACING["margin"], 2)
        self._row.setSpacing(SPACING["gap"])
        self.title = QLabel(tr("legend.title"))
        self.title.setObjectName("legend_title")
        self.title.setToolTip(tr("legend.tip"))
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
            chip = LegendChip(e)
            chip.setToolTip(
                f"{help_text.section_tooltip(e.key)}\n" + tr("legend.chip_tip", label=e.label)
            )
            chip.clicked.connect(lambda _=False, k=e.key: self.section_clicked.emit(k))
            self._row.addWidget(chip, 1)
            self.buttons[e.key] = chip
        self.recolor()

    def recolor(self) -> None:
        """Apply section colors for the current light/dark palette."""
        for key, chip in self.buttons.items():
            chip.set_color(QColor(C.section_color(key, self.dark())))

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type().name == "PaletteChange":
            self.recolor()
