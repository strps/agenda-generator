"""Delayed-expand tooltips: a short text on hover, short + detail after HOVER_EXPAND_MS."""

from PySide6.QtCore import QEvent, QObject, QPoint, QTimer
from PySide6.QtWidgets import QAbstractScrollArea, QToolTip, QWidget

HOVER_EXPAND_MS = 1500  # hover delay before a tooltip adds its detailed text


def make_expand_timer(parent: QObject, slot) -> QTimer:
    """Single-shot timer (interval HOVER_EXPAND_MS) whose timeout calls ``slot``."""
    timer = QTimer(parent)
    timer.setSingleShot(True)
    timer.setInterval(HOVER_EXPAND_MS)
    timer.timeout.connect(slot)
    return timer


class ExpandingToolTip(QObject):
    """Event filter giving one widget a two-stage tooltip (short, then short + detail)."""

    def __init__(self, widget: QWidget, short: str, detail: str) -> None:
        super().__init__(widget)
        self._widget = widget
        self._short = short
        self._detail = detail
        self._text = ""
        self._last_pos: QPoint | None = None
        self.expanded = False
        self.expand_timer = make_expand_timer(self, self._expand)
        self._targets: tuple[QObject, ...] = (widget,)
        widget.installEventFilter(self)
        if isinstance(widget, QAbstractScrollArea):
            viewport = widget.viewport()
            viewport.installEventFilter(self)
            self._targets = (widget, viewport)
        widget.setToolTip(short)

    def _compose(self) -> str:
        return f"{self._short}\n{self._detail}" if self.expanded else self._short

    def current_text(self) -> str:
        return self._text

    def hover(self, global_pos: QPoint | None = None) -> str:
        """Handle a tooltip request; return (and show, if positioned) the current text."""
        if not self.expanded and not self.expand_timer.isActive():
            self.expand_timer.start()
        if global_pos is not None:
            self._last_pos = global_pos
        self._text = self._compose()
        if global_pos is not None:
            QToolTip.showText(global_pos, self._text, self._widget)
        return self._text

    def _start(self) -> None:
        if not self.expanded and not self.expand_timer.isActive():
            self.expand_timer.start()

    def _expand(self) -> None:
        self.expanded = True
        self._text = self._compose()
        if self._last_pos is not None:
            QToolTip.showText(self._last_pos, self._text, self._widget)

    def reset(self) -> None:
        self.expand_timer.stop()
        self.expanded = False
        self._text = ""
        self._last_pos = None
        QToolTip.hideText()

    def set_texts(self, short: str, detail: str) -> None:
        self._short = short
        self._detail = detail
        self._widget.setToolTip(short)
        self.reset()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj not in self._targets:
            return False
        t = event.type()
        if t == QEvent.Type.Enter:
            self._start()
            return False
        if t == QEvent.Type.ToolTip:
            self.hover(event.globalPos())
            return True
        if t in (QEvent.Type.Leave, QEvent.Type.Hide):
            self.reset()
            return False
        return False
