"""Export dialog: edits the export options of a settings dict; all rules live in ``export_model``."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from agenda.gui import export_model as EM
from agenda.gui import help_text
from agenda.gui import settings_model as M
from agenda.gui.hover_tooltip import ExpandingToolTip

_BIG = 10**9
_LAYOUT_FIELDS = {"imposition", "spreads"}  # represented by the layout radio buttons
_LAYOUT_LABELS = {"pages": "Single pages", "spreads": "Spreads", "booklets": "Booklets"}


class ExportDialog(QDialog):
    """Pick export options; ``result_values()`` returns the full values with edits applied."""

    def __init__(
        self,
        values: Mapping[str, Any],
        total_pages: int = 0,
        open_after: bool = False,
        page_range: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("export_dialog")
        self.setWindowTitle("Export PDF")
        self._values: dict[str, Any] = {**M.default_values(), **values}
        self._specs = {s.name: s for s in M.field_specs()}
        self._loading = True
        self.controls: dict[str, QWidget] = {}
        self.tooltips: list[ExpandingToolTip] = []
        self.rows: dict[str, list[QWidget]] = {}
        self.layout_buttons: dict[str, QRadioButton] = {}

        root = QVBoxLayout(self)
        groups: dict[str, QFormLayout] = {}
        for title, fields in EM.EXPORT_FIELDS:
            if title == "Output":
                title = "Range & output"
            box = QGroupBox(title)
            box.setObjectName("group_" + title.lower().replace(" & ", "_").replace(" ", "_"))
            form = QFormLayout(box)
            groups[title] = form
            root.addWidget(box)
            if title == "Layout":
                self._add_layout_radios(form)
            for name in fields:
                if name in _LAYOUT_FIELDS or name in ("output", "debug_grid"):
                    continue
                self._add_field(form, name)

        out = groups["Range & output"]
        self.page_range_edit = QLineEdit(page_range)
        self.page_range_edit.setObjectName("page_range")
        self.page_range_edit.setPlaceholderText(
            f"all ({total_pages} pages)" if total_pages else "all"
        )
        self.page_range_edit.textChanged.connect(self._edited)
        self._add_row(
            out,
            "page_range",
            "page range",
            self.page_range_edit,
            "page_range",
            help_text.EXPORT_HELP,
        )

        self.output_edit = QLineEdit()
        self.output_edit.setObjectName("export_output")
        self.output_edit.textChanged.connect(self._edited)
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setObjectName("browse_output")
        self.browse_button.clicked.connect(self._browse)
        row = QWidget()
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.addWidget(self.output_edit, 1)
        h.addWidget(self.browse_button)
        self._add_row(out, "output", "output", row, "output")
        self.controls["output"] = self.output_edit
        self._tip(self.output_edit, *self._param("output"))
        self._tip(self.browse_button, *self._help("browse_output"))
        self.controls["browse_output"] = self.browse_button

        self._add_field(out, "debug_grid")

        self.open_after_box = QCheckBox("open after export")
        self.open_after_box.setObjectName("open_after")
        self.open_after_box.setChecked(bool(open_after))
        self.open_after_box.toggled.connect(self._edited)
        self.controls["open_after"] = self.open_after_box
        self._tip(self.open_after_box, *self._help("open_after"))
        out.addRow(self.open_after_box)

        self.cli_line = QLineEdit()
        self.cli_line.setObjectName("cli_line")
        self.cli_line.setReadOnly(True)
        cli_label = QLabel("equivalent command")
        self._tip(self.cli_line, *self._help("cli_preview"))
        self._tip(cli_label, *self._help("cli_preview"))
        self.controls["cli_line"] = self.cli_line
        root.addWidget(cli_label)
        root.addWidget(self.cli_line)

        self.error_label = QLabel("")
        self.error_label.setObjectName("error_label")
        self.error_label.setWordWrap(True)
        root.addWidget(self.error_label)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Export")
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        root.addWidget(self.buttons)

        self._load_editors()
        self._loading = False
        self._refresh()

    # --- construction helpers ---
    @staticmethod
    def _param(name: str) -> tuple[str, str]:
        return help_text.PARAM_SHORT[name], help_text.PARAM_DETAILS[name]

    @staticmethod
    def _help(key: str) -> tuple[str, str]:
        return help_text.EXPORT_HELP[key], help_text.EXPORT_HELP[key + "_detail"]

    def _tip(self, widget: QWidget, short: str, detail: str) -> None:
        self.tooltips.append(ExpandingToolTip(widget, short, detail))

    def _add_row(
        self,
        form: QFormLayout,
        name: str,
        text: str,
        widget: QWidget,
        key: str,
        source: Mapping[str, str] | None = None,
    ) -> None:
        label = QLabel(text)
        label.setObjectName(f"label_{name}")
        form.addRow(label, widget)
        self.rows[name] = [label, widget]
        if source is not None:
            short, detail = source[key], source[key + "_detail"]
            self._tip(widget, short, detail)
            self._tip(label, short, detail)
            self.controls[name] = widget

    def _add_layout_radios(self, form: QFormLayout) -> None:
        self.layout_group = QButtonGroup(self)
        for layout in EM.LAYOUTS:
            rb = QRadioButton(_LAYOUT_LABELS[layout])
            rb.setObjectName(f"layout_{layout}")
            self.layout_group.addButton(rb)
            self.layout_buttons[layout] = rb
            self.controls[f"layout_{layout}"] = rb
            self._tip(rb, *self._help(f"layout_{layout}"))
            rb.toggled.connect(lambda on, lay=layout: on and self._layout_chosen(lay))
            form.addRow(rb)

    def _add_field(self, form: QFormLayout, name: str) -> None:
        spec = self._specs[name]
        k = spec.kind
        w: QWidget
        if k == M.BOOL:
            w = QCheckBox()
            w.toggled.connect(self._edited)
        elif k in (M.CHOICE, M.OPT_CHOICE):
            w = QComboBox()
            for c in spec.choices:
                w.addItem(c, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.INT:
            w = QSpinBox()
            w.setRange(int(spec.minimum) if spec.minimum is not None else -_BIG, _BIG)
            if spec.maximum is not None:
                w.setMaximum(int(spec.maximum))
            w.valueChanged.connect(self._edited)
        elif k == M.FLOAT:
            w = QDoubleSpinBox()
            w.setRange(spec.minimum if spec.minimum is not None else -_BIG, _BIG)
            w.setDecimals(2)
            w.valueChanged.connect(self._edited)
        else:  # text, auto_int: edited as text, parsed by Config
            w = QLineEdit()
            w.textEdited.connect(self._edited)
        label = QLabel(name.replace("_", " "))
        label.setObjectName(f"label_{name}")
        form.addRow(label, w)
        self.rows[name] = [label, w]
        self.controls[name] = w
        short, detail = self._param(name)
        self._tip(w, short, detail)
        self._tip(label, short, detail)

    # --- values <-> editors ---
    def _field_names(self) -> list[str]:
        return [n for n in EM.export_field_names() if n not in _LAYOUT_FIELDS and n != "output"]

    def _load_editors(self) -> None:
        was, self._loading = self._loading, True
        try:
            for name in self._field_names():
                w, v = self.controls[name], self._values[name]
                k = self._specs[name].kind
                if k == M.BOOL:
                    w.setChecked(bool(v))  # type: ignore[attr-defined]
                elif k in (M.CHOICE, M.OPT_CHOICE):
                    w.setCurrentIndex(max(w.findData(v), 0))  # type: ignore[attr-defined]
                elif k == M.INT:
                    w.setValue(int(v))  # type: ignore[attr-defined]
                elif k == M.FLOAT:
                    w.setValue(float(v))  # type: ignore[attr-defined]
                else:
                    w.setText(str(v))  # type: ignore[attr-defined]
            self.output_edit.setText(str(self._values["output"]))
            self.layout_buttons[EM.layout_of(self._values)].setChecked(True)
        finally:
            self._loading = was

    def _read_editors(self) -> None:
        for name in self._field_names():
            w, k = self.controls[name], self._specs[name].kind
            if k == M.BOOL:
                v: Any = w.isChecked()  # type: ignore[attr-defined]
            elif k in (M.CHOICE, M.OPT_CHOICE):
                v = w.currentData()  # type: ignore[attr-defined]
            elif k in (M.INT, M.FLOAT):
                v = w.value()  # type: ignore[attr-defined]
            else:
                v = w.text().strip()  # type: ignore[attr-defined]
                if k == M.AUTO_INT:
                    v = int(v) if v.isdigit() else (v or "auto")
            self._values[name] = v
        self._values["output"] = self.output_edit.text().strip()

    def _layout_chosen(self, layout: str) -> None:
        if self._loading:
            return
        self._read_editors()
        self._values = EM.with_layout(self._values, layout)
        self._load_editors()
        self._refresh()

    def _edited(self, *_: object) -> None:
        if self._loading:
            return
        self._read_editors()
        self._refresh()

    def _refresh(self) -> None:
        for name, widgets in self.rows.items():
            on = EM.field_enabled(self._values, name)
            for w in widgets:
                w.setEnabled(on)
        for name in ("booklet_folded",):
            self.controls[name].setEnabled(EM.field_enabled(self._values, name))
        self.page_range_edit.setEnabled(EM.field_enabled(self._values, "page_range"))
        err = EM.validate(self._values, self.page_range())
        self.error_label.setText(err)
        self.ok_button.setEnabled(not err)
        self.cli_line.setText(EM.cli_command(self._values, self.page_range()))

    def _browse(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", self.output_edit.text(), "PDF (*.pdf)"
        )
        if path:
            self.output_edit.setText(str(EM.ensure_pdf(path)))

    # --- results ---
    def result_values(self) -> dict[str, Any]:
        """Settings values with the export fields edited; all other keys are untouched."""
        self._read_editors()
        return dict(self._values)

    def page_range(self) -> str:
        return self.page_range_edit.text().strip()

    def open_after(self) -> bool:
        return self.open_after_box.isChecked()
