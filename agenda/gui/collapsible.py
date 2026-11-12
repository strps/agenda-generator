"""Collapsible settings section: arrow toggle, optional enable box, form body."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QEvent, QObject, QSize, Qt, QVariantAnimation, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from agenda.gui.style_model import SPACING
from agenda.uitext import tr

BOX_KINDS = ("planner", "page", "count")
ANIM_MS = 160


class _Clip(QWidget):
    """Shows the top `limit` px of `inner` (all of it when None); `inner` keeps its natural size."""

    def __init__(self, inner: QWidget) -> None:
        super().__init__()
        self.inner = inner
        self.limit: int | None = None
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        inner.setParent(self)
        inner.installEventFilter(self)

    def natural_height(self, width: int | None = None) -> int:
        width = self.width() if width is None else width
        h = self.inner.heightForWidth(width) if self.inner.hasHeightForWidth() else -1
        return (
            h
            if h >= 0
            else max(self.inner.sizeHint().height(), self.inner.minimumSizeHint().height())
        )

    def _height(self, width: int | None = None) -> int:
        return self.natural_height(width) if self.limit is None else self.limit

    def hasHeightForWidth(self) -> bool:
        return self.inner.hasHeightForWidth()

    def heightForWidth(self, width: int) -> int:
        return self._height(width)

    def sizeHint(self) -> QSize:
        return QSize(self.inner.sizeHint().width(), self._height())

    def minimumSizeHint(self) -> QSize:
        return QSize(self.inner.minimumSizeHint().width(), self._height())

    def set_limit(self, limit: int | None) -> None:
        self.limit = limit
        self._relayout()

    def _relayout(self) -> None:  # also used by _Slide
        """Lay out the ancestors now: nested clips would otherwise settle one event loop pass per
        level, and the frames in between show stale sizes."""
        self.updateGeometry()
        chain = []
        w = self.parentWidget()
        while w is not None:
            chain.append(w)
            w = w.parentWidget()
        for w in chain:  # invalidate explicitly: updateGeometry() is a no-op while hidden
            if w.layout() is not None:
                w.layout().invalidate()
        for w in chain:  # innermost first; an enclosing clip re-sizes its inner
            if isinstance(w, _Clip):
                w.inner.setGeometry(0, 0, w.width(), w.natural_height())
                w.updateGeometry()
            elif w.layout() is not None:
                w.layout().activate()

    def resizeEvent(self, event) -> None:
        self.inner.setGeometry(0, 0, self.width(), self.natural_height())
        super().resizeEvent(event)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self.inner and event.type() == QEvent.Type.LayoutRequest:
            self.inner.setGeometry(0, 0, self.width(), self.natural_height())
            self._relayout()
        return False


class _Slide(QObject):
    """Shows or hides `body` (wrapped in `clip`): instantly, or as a slide of its height."""

    def __init__(self, body: QWidget, parent: QWidget) -> None:
        super().__init__(parent)
        self.body = body
        self.clip = _Clip(body)
        self.target = False
        self._anim = QVariantAnimation(self)
        self._anim.setDuration(ANIM_MS)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(lambda v: self.clip.set_limit(int(v)))
        self._anim.finished.connect(lambda: self.show(self.target))

    def show(self, on: bool) -> None:
        self.target = on
        self._anim.stop()
        self.clip.limit = None
        self.body.setVisible(on)
        self.clip.setVisible(on)
        self.clip._relayout()

    def slide(self, on: bool) -> None:
        self.target = on
        if self._anim.state() == QVariantAnimation.State.Running:
            start = self.clip.limit or 0
        else:
            start = self.clip.height() if self.clip.isVisible() else 0
        self._anim.stop()
        self.clip.set_limit(start)
        self.body.setVisible(True)
        self.clip.setVisible(True)
        self._anim.setStartValue(start)
        self._anim.setEndValue(self.clip.natural_height() if on else 0)
        self._anim.start()


class _Expandable:
    """Arrow-toggle behaviour: user clicks slide, set_expanded is instant. Needs `toggle_button`, `_slide`, `_animate`, `_refresh_text` and `expanded_changed`."""

    def _toggled(self, on: bool) -> None:
        self._refresh_text(on)
        if self._animate and self.isVisible():
            self._slide.slide(on)
        else:
            self._slide.show(on)
        self.expanded_changed.emit(on)

    def set_expanded(self, on: bool) -> None:
        if self.toggle_button.isChecked() == on:
            self._refresh_text(on)
            self._slide.show(on)
            return
        self._animate = False
        try:
            self.toggle_button.setChecked(on)
        finally:
            self._animate = True

    def is_expanded(self) -> bool:
        return self.toggle_button.isChecked()


class CollapsibleSection(_Expandable, QFrame):
    """Header with `toggle_button` (+ `enable_box` unless enable == "none") and a `body` with `form`."""

    expanded_changed = Signal(bool)
    enable_toggled = Signal(bool)  # user toggles only
    pressed = Signal()  # any mouse press inside the section

    def __init__(self, key: str, title: str, enable: str = "none") -> None:
        super().__init__()
        self.key = key
        self.setObjectName(f"section_{key}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        header = QFrame()
        header.setObjectName("collapsible_header")  # hover tint spans the toggle and the box
        header.setAttribute(Qt.WidgetAttribute.WA_Hover)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(SPACING["gap"], 2, SPACING["gap"], 2)
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("section_toggle")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setFlat(True)
        self._title = title
        hl.addWidget(self.toggle_button, 1)
        self.pad_label = QLabel()  # badge naming the padding/filler uses of this section's page
        self.pad_label.setObjectName("section_pad")
        self.pad_label.setVisible(False)
        hl.addWidget(self.pad_label)
        self.enable_box: QCheckBox | None = None
        if enable in BOX_KINDS:
            self.enable_box = QCheckBox()
            self.enable_box.setObjectName("section_enable")
            self.enable_box.setChecked(True)
            self.enable_box.setToolTip(tr("section.include_tip"))
            self.enable_box.toggled.connect(self._box_toggled)
            hl.addWidget(self.enable_box)
        lay.addWidget(header)
        self.body = QWidget()
        self.body.setObjectName("section_body")
        self.form = QFormLayout(self.body)
        self.form.setSpacing(SPACING["gap"])
        gap, margin = SPACING["gap"], SPACING["margin"]
        self.form.setContentsMargins(margin, gap, margin, margin)
        self._slide = _Slide(self.body, self)  # the slide reveals the body, never squeezes it
        self._clip = self._slide.clip
        lay.addWidget(self._clip)
        self._animate = True  # user clicks slide; set_expanded is instant
        self.collapsible = True
        self.toggle_button.toggled.connect(self._toggled)
        self.set_expanded(False)

    def mousePressEvent(self, event) -> None:
        self.pressed.emit()
        super().mousePressEvent(event)

    def set_static(self, open_body: bool) -> None:
        """No arrow: a plain header (title and enable box) over a body that is always shown
        (``open_body``) or never."""
        self.set_expanded(False)
        self.collapsible = False
        self.toggle_button.setCheckable(False)
        self._refresh_text(False)
        self._slide.show(open_body)

    def _refresh_text(self, expanded: bool) -> None:
        title = self._title.replace("&", "&&")  # a lone & would be a mnemonic
        if self.collapsible:
            title = f"{'▾' if expanded else '▸'} {title}"
        self.toggle_button.setText(title)

    @property
    def title(self) -> str:
        return self._title

    def _box_toggled(self, on: bool) -> None:
        self.body.setEnabled(on)
        self.enable_toggled.emit(on)

    def set_enabled_state(self, on: bool) -> None:
        if self.enable_box is not None:
            self.enable_box.blockSignals(True)
            self.enable_box.setChecked(on)
            self.enable_box.blockSignals(False)
        self.body.setEnabled(on)

    def set_pad_use(self, label: str) -> None:
        """Badge ``label`` and ring the enable box: the page is printed as padding or filler
        ("" = not used that way)."""
        self.pad_label.setText(label)
        self.pad_label.setVisible(bool(label))
        box = self.enable_box
        if box is not None and box.property("pad") != bool(label):
            box.setProperty("pad", bool(label))
            box.style().unpolish(box)
            box.style().polish(box)

    def enabled_state(self) -> bool:
        return self.enable_box.isChecked() if self.enable_box is not None else True
