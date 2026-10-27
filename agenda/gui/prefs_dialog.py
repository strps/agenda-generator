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
from agenda.uitext import LANGUAGES, tr


class GuiSettingsDialog(QDialog):
    """Holds the app appearance. No QSettings access: the caller reads and writes."""

    def __init__(
        self,
        appearance: str = SM.DEFAULT_APPEARANCE,
        parent: QWidget | None = None,
        ui_language: str = "system",
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("prefs.title"))
        self.setObjectName("prefs_dialog")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        self.appearance_box = QComboBox()
        self.appearance_box.setObjectName("appearance")
        for value in SM.APPEARANCES:
            self.appearance_box.addItem(tr(f"prefs.appearance.{value}"), value)
        chosen = appearance if appearance in SM.APPEARANCES else SM.DEFAULT_APPEARANCE
        self.appearance_box.setCurrentIndex(self.appearance_box.findData(chosen))
        label = QLabel(tr("prefs.appearance"))
        label.setObjectName("label_appearance")
        self.appearance_tooltip = ExpandingToolTip(
            self.appearance_box, help_text.TOOLTIPS["appearance"], ""
        )
        self.label_tooltip = ExpandingToolTip(label, help_text.TOOLTIPS["appearance"], "")
        form.addRow(label, self.appearance_box)
        self.language_box = QComboBox()
        self.language_box.setObjectName("ui_language")
        for value in ("system", *LANGUAGES):
            self.language_box.addItem(tr(f"prefs.language.{value}"), value)
        chosen_lang = ui_language if ui_language in LANGUAGES else "system"
        self.language_box.setCurrentIndex(self.language_box.findData(chosen_lang))
        lang_label = QLabel(tr("prefs.language"))
        lang_label.setObjectName("label_ui_language")
        self.language_tooltip = ExpandingToolTip(
            self.language_box, help_text.TOOLTIPS["ui_language"], ""
        )
        self.language_label_tooltip = ExpandingToolTip(
            lang_label, help_text.TOOLTIPS["ui_language"], ""
        )
        form.addRow(lang_label, self.language_box)
        lay.addLayout(form)
        note = QLabel(help_text.TOOLTIPS["preferences"])
        note.setWordWrap(True)
        lay.addWidget(note)
        self._initial_language = chosen_lang
        self.restart_note = QLabel(tr("prefs.restart_note"))
        self.restart_note.setObjectName("restart_note")
        self.restart_note.setWordWrap(True)
        self.restart_note.setVisible(False)
        lay.addWidget(self.restart_note)
        self.language_box.currentIndexChanged.connect(self._language_changed)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def appearance(self) -> str:
        return str(self.appearance_box.currentData())

    def ui_language(self) -> str:
        return str(self.language_box.currentData())

    def _language_changed(self) -> None:
        self.restart_note.setVisible(self.ui_language() != self._initial_language)
