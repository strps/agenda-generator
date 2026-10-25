"""Section bar widget: paints the geometry from `bar_model` (no layout logic here)."""

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from agenda.gui import bar_model as B

PLACEHOLDER = QColor("#8a8984")  # neutral until task 7 adds the section palette
TICK_H = 6
MARKER_W = 2


class SectionBar(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("section_bar")
        self.setFixedHeight(40)
        self.plan: list = []
        self.index = 0

    def set_plan(self, plan) -> None:
        self.plan = list(plan)
        self.update()

    def set_position(self, index: int) -> None:
        self.index = index
        self.update()

    def geometry_for(self, width: float | None = None) -> B.BarGeometry:
        return B.geometry(self.plan, float(self.width() if width is None else width))

    def paintEvent(self, _event) -> None:
        geo = self.geometry_for()
        p = QPainter(self)
        bar_h = self.height() - TICK_H - 2
        for s in geo.segments():
            rect = QRectF(s.x, 0, s.width, bar_h)
            p.fillRect(rect, PLACEHOLDER)
            if s.padding:
                p.fillRect(
                    rect, QBrush(self.palette().window().color(), Qt.BrushStyle.BDiagPattern)
                )
        p.setPen(QPen(self.palette().text().color(), 1))
        for x in geo.ticks():
            p.drawLine(QPointF(x, bar_h), QPointF(x, bar_h + TICK_H))
        if geo.total:
            p.setPen(QPen(self.palette().highlight().color(), MARKER_W))
            mx = geo.marker_x(self.index)
            p.drawLine(QPointF(mx, 0), QPointF(mx, bar_h))
        p.end()
