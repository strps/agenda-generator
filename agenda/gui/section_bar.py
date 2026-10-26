"""Section bar widget: paints the geometry from `bar_model` (no layout logic here)."""

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QToolTip, QWidget

from agenda.gui import bar_model as B
from agenda.gui import help_text
from agenda.gui import section_colors as C
from agenda.gui.hover_tooltip import HOVER_EXPAND_MS, make_expand_timer  # noqa: F401

TICK_H = 6
MARKER_W = 2


KEYS = {
    Qt.Key.Key_Left: "left",
    Qt.Key.Key_Right: "right",
    Qt.Key.Key_PageUp: "pageup",
    Qt.Key.Key_PageDown: "pagedown",
    Qt.Key.Key_Home: "home",
    Qt.Key.Key_End: "end",
}


class SectionBar(QWidget):
    page_requested = Signal(int)  # 0-based plan index from click, drag or keyboard

    def __init__(self) -> None:
        super().__init__()
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setObjectName("section_bar")
        self.setFixedHeight(40)
        self.plan: list = []
        self.index = 0
        self._hover_key: str | None = None
        self._hover_text = ""
        self._expanded = False
        self._last_pos: QPoint | None = None
        self.expand_timer = make_expand_timer(self, self._expand)

    def set_plan(self, plan) -> None:
        self.plan = list(plan)
        self.reset_hover()
        self.update()

    def set_position(self, index: int) -> None:
        self.index = index
        self.update()

    def geometry_for(self, width: float | None = None) -> B.BarGeometry:
        return B.geometry(self.plan, float(self.width() if width is None else width))

    def page_at(self, x: float) -> int | None:
        return self.geometry_for().page_at(x)

    def tooltip_for(self, x: float) -> str:
        i = self.page_at(x)
        return "" if i is None else B.tooltip_text(self.plan, i)

    def _section_key(self, i: int) -> str:
        e = self.plan[i]
        return B.PADDING if e.kind == "padding" else e.section

    def current_tooltip(self) -> str:
        return self._hover_text

    def reset_hover(self) -> None:
        self.expand_timer.stop()
        self._hover_key = None
        self._hover_text = ""
        self._expanded = False
        QToolTip.hideText()

    def _compose(self, short: str) -> str:
        if self._expanded and self._hover_key is not None:
            return f"{short}\n{help_text.section_tooltip(self._hover_key)}"
        return short

    def hover_at(self, x: float, global_pos: QPoint | None = None) -> str:
        """Update hover state for bar-x ``x``; return the tooltip text to show."""
        i = self.page_at(x)
        if i is None:
            self.reset_hover()
            return ""
        key = self._section_key(i)
        if key != self._hover_key:
            self._hover_key = key
            self._expanded = False
            self.expand_timer.start()
        if global_pos is not None:
            self._last_pos = global_pos
        self._hover_text = self._compose(B.tooltip_text(self.plan, i))
        if global_pos is not None:
            QToolTip.showText(global_pos, self._hover_text, self)
        return self._hover_text

    def _expand(self) -> None:
        if self._hover_key is None:
            return
        self._expanded = True
        head = self._hover_text.split("\n", 1)[0]
        self._hover_text = self._compose(head)
        if self._last_pos is not None:
            QToolTip.showText(self._last_pos, self._hover_text, self)

    def leaveEvent(self, event) -> None:
        self.reset_hover()
        super().leaveEvent(event)

    def first_page_of(self, section: str) -> int | None:
        """Legend click target: emit and return the first page of ``section``."""
        i = B.first_page_of(self.plan, section)
        if i is not None:
            self._request(i)
        return i

    def _request(self, index: int) -> None:
        self.set_position(index)
        self.page_requested.emit(index)

    def _scrub(self, event) -> None:
        if (i := self.page_at(event.position().x())) is not None and i != self.index:
            self._request(i)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.reset_hover()
            self.setFocus()
            self._scrub(event)

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self.reset_hover()
            self._scrub(event)
        else:
            self.hover_at(event.position().x(), event.globalPosition().toPoint())

    def keyPressEvent(self, event) -> None:
        key = KEYS.get(event.key())
        if key is None or not self.plan:
            super().keyPressEvent(event)
            return
        self._request(B.key_target(key, self.index, self.plan))

    def dark(self) -> bool:
        return C.is_dark(self.palette().window().color().lightness())

    def color_for(self, key: str) -> QColor:
        return QColor(C.section_color(key, self.dark()))

    def paintEvent(self, _event) -> None:
        geo = self.geometry_for()
        p = QPainter(self)
        bar_h = self.height() - TICK_H - 2
        for s in geo.segments():
            rect = QRectF(s.x, 0, s.width, bar_h)
            p.fillRect(rect, self.color_for(s.section))
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
