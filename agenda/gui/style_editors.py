"""Editors for the PDF style fields: ColorEdit (hex + swatch + clear) and FontEdit (name or file).

Qt dialogs are opened by small methods (`_pick_color`, `_pick_file`) so tests can replace them.
Widgets only hold text; ``Config`` validates it.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLineEdit,
    QToolButton,
    QWidget,
)

from agenda import fonts
from agenda.gui import help_text
from agenda.themes import rgb_to_hex


class ColorEdit(QWidget):
    """Hex text + swatch button (opens a color dialog) + clear button (back to the theme color)."""

    edited = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._fallback = "#000000"
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.line = QLineEdit()
        self.line.setPlaceholderText("theme default")
        self.swatch = QToolButton()
        self.swatch.setObjectName("color_swatch")
        self.swatch.setFixedSize(24, 24)
        self.swatch.setToolTip(help_text.TOOLTIPS["color_swatch"])
        self.clear_button = QToolButton()
        self.clear_button.setObjectName("color_clear")
        self.clear_button.setText("x")
        self.clear_button.setToolTip(help_text.TOOLTIPS["color_clear"])
        lay.addWidget(self.swatch)
        lay.addWidget(self.line, 1)
        lay.addWidget(self.clear_button)
        self.line.textEdited.connect(self._typed)
        self.swatch.clicked.connect(self._choose)
        self.clear_button.clicked.connect(lambda: self.set_value(None))
        self._paint()

    def value(self) -> str | None:
        return self.line.text().strip() or None

    def set_value(self, value: str | None) -> None:
        text = "" if value is None else str(value)
        if text == self.line.text():
            return
        self.line.setText(text)
        self._paint()
        self.edited.emit()

    def set_fallback(self, rgb: tuple[int, int, int]) -> None:
        """Theme color shown by the swatch while no override is set."""
        self._fallback = rgb_to_hex(rgb)
        self._paint()

    def swatch_color(self) -> str:
        """Effective color: the override when it is a valid color, else the theme color."""
        text = self.value()
        if text:
            c = QColor(text if text.startswith("#") else "#" + text)
            if c.isValid():
                return c.name()
        return self._fallback

    def _typed(self, _text: str) -> None:
        self._paint()
        self.edited.emit()

    def _paint(self) -> None:
        self.swatch.setStyleSheet(f"background-color: {self.swatch_color()};")

    def _pick_color(self, initial: str) -> str | None:
        c = QColorDialog.getColor(QColor(initial), self)
        return c.name() if c.isValid() else None

    def _choose(self) -> None:
        picked = self._pick_color(self.swatch_color())
        if picked:
            self.set_value(picked)


class FontEdit(QWidget):
    """Editable combo of built-in font names + Browse button for a .ttf/.otf file."""

    edited = Signal()

    def __init__(self) -> None:
        super().__init__()
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.combo = QComboBox()
        self.combo.setEditable(True)
        for name in fonts.BUILTIN:
            self.combo.addItem(name)
        self.browse_button = QToolButton()
        self.browse_button.setObjectName("font_browse")
        self.browse_button.setText("Browse...")
        self.browse_button.setToolTip(help_text.TOOLTIPS["font_browse"])
        lay.addWidget(self.combo, 1)
        lay.addWidget(self.browse_button)
        self.combo.editTextChanged.connect(lambda _t: self.edited.emit())
        self.browse_button.clicked.connect(self._browse)

    def value(self) -> str:
        return self.combo.currentText().strip()

    def set_value(self, value: str) -> None:
        self.combo.setEditText(str(value))

    def _pick_file(self) -> str:
        path, _ = QFileDialog.getOpenFileName(self, "Font file", "", "Fonts (*.ttf *.otf)")
        return path

    def _browse(self) -> None:
        path = self._pick_file()
        if path:
            self.set_value(path)
