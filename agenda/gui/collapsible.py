"""Collapsible settings section: a header (arrow toggle plus optional enable box) over a form body."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QToolButton,
    QVBoxLayout,
    QWidget,
)
from agenda.gui.style_model import SPACING

BOX_KINDS = ("planner", "page", "count")


class CollapsibleSection(QFrame):
    """Header with `toggle_button` (+ `enable_box` unless enable == "none") and a `body` with `form`."""

    expanded_changed = Signal(bool)
    enable_toggled = Signal(bool)  # user toggles only

    def __init__(self, key: str, title: str, enable: str = "none") -> None:
        super().__init__()
        self.key = key
        self.setObjectName(f"section_{key}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(SPACING["gap"], 2, SPACING["gap"], 2)
        self.toggle_button = QToolButton()
        self.toggle_button.setObjectName("section_toggle")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle_button.setAutoRaise(True)
        self._title = title
        hl.addWidget(self.toggle_button, 1)
        self.enable_box: QCheckBox | None = None
        if enable in BOX_KINDS:
            self.enable_box = QCheckBox()
            self.enable_box.setObjectName("section_enable")
            self.enable_box.setChecked(True)
            self.enable_box.setToolTip("Include this template in the agenda.")
            self.enable_box.toggled.connect(self._box_toggled)
            hl.addWidget(self.enable_box)
        lay.addWidget(header)
        self.body = QWidget()
        self.form = QFormLayout(self.body)
        self.form.setSpacing(SPACING["gap"])
        gap, margin = SPACING["gap"], SPACING["margin"]
        self.form.setContentsMargins(margin, gap, margin, margin)
        lay.addWidget(self.body)
        self.toggle_button.toggled.connect(self._toggled)
        self.set_expanded(False)

    def _refresh_text(self, expanded: bool) -> None:
        arrow = "▾" if expanded else "▸"
        self.toggle_button.setText(f"{arrow} {self._title}")

    @property
    def title(self) -> str:
        return self._title

    def _toggled(self, on: bool) -> None:
        self._refresh_text(on)
        self.body.setVisible(on)
        self.expanded_changed.emit(on)

    def set_expanded(self, on: bool) -> None:
        if self.toggle_button.isChecked() == on:
            self._refresh_text(on)
            self.body.setVisible(on)
            return
        self.toggle_button.setChecked(on)

    def is_expanded(self) -> bool:
        return self.toggle_button.isChecked()

    def _box_toggled(self, on: bool) -> None:
        self.body.setEnabled(on)
        self.enable_toggled.emit(on)

    def set_enabled_state(self, on: bool) -> None:
        if self.enable_box is not None:
            self.enable_box.blockSignals(True)
            self.enable_box.setChecked(on)
            self.enable_box.blockSignals(False)
        self.body.setEnabled(on)

    def enabled_state(self) -> bool:
        return self.enable_box.isChecked() if self.enable_box is not None else True
