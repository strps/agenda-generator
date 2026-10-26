"""GUI Settings (Preferences) dialog: application look only, never the PDF."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from agenda.gui import help_text
from agenda.gui import style_model as SM
from agenda.gui.hover_tooltip import ExpandingToolTip


class GuiSettingsDialog(QDialog):
    """Holds the app appearance. No QSettings access: the caller reads and writes."""

    def __init__(self, appearance: str = SM.DEFAULT_APPEARANCE, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setObjectName("prefs_dialog")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.appearance_box = QComboBox()
        self.appearance_box.setObjectName("appearance")
        self.appearance_box.addItems(list(SM.APPEARANCES))
        self.appearance_box.setCurrentText(
            appearance if appearance in SM.APPEARANCES else SM.DEFAULT_APPEARANCE
        )
        label = QLabel("Appearance")
        label.setObjectName("label_appearance")
        self.appearance_tooltip = ExpandingToolTip(
            self.appearance_box, help_text.TOOLTIPS["appearance"], ""
        )
        self.label_tooltip = ExpandingToolTip(label, help_text.TOOLTIPS["appearance"], "")
        form.addRow(label, self.appearance_box)
        lay.addLayout(form)
        note = QLabel(help_text.TOOLTIPS["preferences"])
        note.setWordWrap(True)
        lay.addWidget(note)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def appearance(self) -> str:
        return self.appearance_box.currentText()
