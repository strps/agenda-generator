"""Settings form generated from the ``Config`` model (field kinds come from ``settings_model``).

Widgets only hold values; ``Config`` validates them (``config()`` returns it or an error text).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from agenda import templates as T
from agenda import themes
from agenda.catalog import catalog_rows
from agenda.config import Config
from agenda.gui import export_model as EM
from agenda.gui import help_text
from agenda.gui import settings_model as M
from agenda.gui.collapsible import CollapsibleGroup, CollapsibleSection
from agenda.gui.hover_tooltip import ExpandingToolTip
from agenda.gui.style_editors import ColorEdit, FontEdit
from agenda.gui.style_model import SPACING

_BIG = 10**9
SECTION_SWITCHED = ("planners", "pages")  # set by the section boxes, not edited directly


def _join_ints(v: Any) -> str:
    return ",".join(str(i) for i in v) if isinstance(v, list) else str(v)


class SettingsPanel(QFrame):
    """Scrollable form. `changed` fires on any edit; `editors` maps field name -> widget."""

    changed = Signal()
    section_activated = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("settings")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.specs = M.field_specs()
        self.editors: dict[str, QWidget] = {}
        self.page_boxes: dict[str, QCheckBox] = {}
        self.tooltips: dict[str, ExpandingToolTip] = {}
        self.label_tooltips: dict[str, ExpandingToolTip] = {}
        self._extra_pages: list[str] = []
        self._loading = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        outer.addWidget(scroll, 1)
        body = QWidget()
        col = QVBoxLayout(body)
        col.setSpacing(SPACING["gap"])
        gap = SPACING["gap"]
        col.setContentsMargins(gap, gap, gap, gap)
        self.sections: dict[str, CollapsibleSection] = {}
        self.groups: dict[str, CollapsibleGroup] = {}
        self._group_of: dict[str, CollapsibleGroup] = {}
        self.active_section = T.GLOBAL
        for sp in T.SECTIONS:
            sec = CollapsibleSection(sp.key, sp.label, sp.enable)
            self.sections[sp.key] = sec
            sec.expanded_changed.connect(lambda on, k=sp.key: on and self.activate(k))
            sec.enable_toggled.connect(lambda on, k=sp.key: self._section_toggled(k, on))
            sec.pressed.connect(lambda k=sp.key: self.activate(k, expand=False))
        for g in T.GROUPS:
            group = CollapsibleGroup(g.key, g.label)
            self.groups[g.key] = group
            col.addWidget(group)
            for key in g.sections:
                group.add(self.sections[key])
                self._group_of[key] = group
            group.set_expanded(g.expanded)
        self.sections[T.GLOBAL].set_expanded(True)
        self.sections[T.GLOBAL].set_active(True)
        self.sections[T.STYLING].toggle_button.setToolTip(help_text.TOOLTIPS["styling_section"])
        shown: set[str] = set()  # sections with at least one visible field
        for spec in self.specs:
            w = self._make(spec)
            self.editors[spec.name] = w
            short = help_text.PARAM_SHORT[spec.name]
            detail = help_text.PARAM_DETAILS[spec.name]
            self.tooltips[spec.name] = ExpandingToolTip(w, short, detail)
            form = self.sections[T.group_of(spec.name)].form
            if spec.kind == M.PAGES:
                form.addRow(w)
            else:
                label = QLabel(spec.name.replace("_", " "))
                label.setObjectName(f"label_{spec.name}")
                self.label_tooltips[spec.name] = ExpandingToolTip(label, short, detail)
                form.addRow(label, w)
            if spec.name in EM.export_field_names() or spec.name in SECTION_SWITCHED:
                # edited in the export dialog or by section boxes; widgets stay (hidden) so
                # values() round-trips
                form.setRowVisible(w, False)
            else:
                shown.add(T.group_of(spec.name))
        for key, sec in self.sections.items():
            if key not in shown:
                sec.set_collapsible(False)
        col.addStretch(1)
        scroll.setWidget(body)
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("settings_error")
        outer.addWidget(self.error_label)
        self.changed.connect(self._sync_boxes)
        self.changed.connect(self._refresh_swatches)
        app = QApplication.instance()
        if app is not None:
            app.focusChanged.connect(lambda _old, new: self.notify_focus(new))
        self.set_values(M.default_values())

    # --- sections ---
    def activate(self, key: str, expand: bool = True) -> None:
        sec = self.sections[key]
        self._group_of[key].set_expanded(True)
        if expand and sec.collapsible and not sec.is_expanded():
            sec.set_expanded(True)  # its expanded_changed handler re-enters and emits
            return
        self.active_section = key
        for k, other in self.sections.items():
            other.set_active(k == key)
        self.section_activated.emit(key)

    def notify_focus(self, widget: QWidget | None) -> None:
        w = widget
        while w is not None:
            if isinstance(w, CollapsibleSection) and self.sections.get(w.key) is w:
                # header focus (a click on the toggle) must not expand: the click itself toggles
                self.activate(w.key, expand=w.body.isAncestorOf(widget))
                return
            w = w.parentWidget()

    def _section_toggled(self, key: str, on: bool) -> None:
        before = self.values()
        after = T.with_enabled(before, key, on)
        self._loading = True
        try:
            for spec in self.specs:
                if after[spec.name] != before[spec.name]:
                    self._set(spec, self.editors[spec.name], after[spec.name])
        finally:
            self._loading = False
        self.changed.emit()

    def _sync_boxes(self) -> None:
        cfg = SimpleNamespace(**self.values())
        for key, sec in self.sections.items():
            if sec.enable_box is not None:
                sec.set_enabled_state(T.is_enabled(cfg, key))

    def _refresh_swatches(self) -> None:
        palette = themes.palette_for(self.values()["theme"])
        for spec in self.specs:
            if spec.kind == M.COLOR:
                w = self.editors[spec.name]
                w.set_fallback(palette[spec.name.removeprefix("color_")])  # type: ignore[attr-defined]

    # --- widget factory ---
    def _make(self, spec: M.FieldSpec) -> QWidget:
        k = spec.kind
        if k == M.BOOL:
            w: QWidget = QCheckBox()
            w.toggled.connect(self._edited)
        elif k in (M.CHOICE, M.OPT_CHOICE):
            w = QComboBox()
            if k == M.OPT_CHOICE:
                w.addItem("(none)", None)
            for c in spec.choices:
                w.addItem(c, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.THEME:
            w = QComboBox()
            for c in spec.choices:
                w.addItem(c, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.COLOR:
            w = ColorEdit()
            w.edited.connect(self._edited)
        elif k == M.FONT:
            w = FontEdit()
            w.edited.connect(self._edited)
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
        elif k == M.MULTI_CHOICE:
            w = QGroupBox()
            lay = QVBoxLayout(w)
            lay.setContentsMargins(4, 2, 4, 2)
            for c in spec.choices:
                cb = QCheckBox(c)
                cb.toggled.connect(self._edited)
                lay.addWidget(cb)
        elif k == M.TEXT_LIST:
            w = QPlainTextEdit()
            w.setPlaceholderText("one per line")
            w.setFixedHeight(60)
            w.textChanged.connect(self._edited)
        elif k == M.PAGES:
            w = self._make_pages()
        else:  # text, path, opt_path, int_list, auto_int: edited as text, parsed by Config
            w = QLineEdit()
            w.textEdited.connect(self._edited)
        return w

    def _make_pages(self) -> QGroupBox:
        box = QGroupBox("pages (none checked = default core pages)")
        lay = QVBoxLayout(box)
        category = None
        for row in catalog_rows():
            if row["category"] != category:
                category = row["category"]
                lay.addWidget(QLabel(f"<b>{category}</b>"))
            cb = QCheckBox(f"{row['name']} ({row['id']})")
            cb.toggled.connect(self._edited)
            self.page_boxes[str(row["id"])] = cb
            lay.addWidget(cb)
        return box

    # --- values ---
    def _edited(self, *_: object) -> None:
        if not self._loading:
            self.changed.emit()

    def values(self) -> dict[str, Any]:
        """Raw widget values keyed by Config field name (unvalidated)."""
        out: dict[str, Any] = {}
        for spec in self.specs:
            w = self.editors[spec.name]
            k = spec.kind
            if k == M.BOOL:
                out[spec.name] = w.isChecked()  # type: ignore[attr-defined]
            elif k in (M.CHOICE, M.OPT_CHOICE, M.THEME):
                out[spec.name] = w.currentData()  # type: ignore[attr-defined]
            elif k in (M.COLOR, M.FONT):
                out[spec.name] = w.value()  # type: ignore[attr-defined]
            elif k in (M.INT, M.FLOAT):
                out[spec.name] = w.value()  # type: ignore[attr-defined]
            elif k == M.MULTI_CHOICE:
                out[spec.name] = [
                    cb.text()
                    for cb in w.findChildren(QCheckBox)
                    if cb.isChecked()  # type: ignore[attr-defined]
                ]
            elif k == M.TEXT_LIST:
                out[spec.name] = M.parse_lines(w.toPlainText())  # type: ignore[attr-defined]
            elif k == M.PAGES:
                ids = [i for i, cb in self.page_boxes.items() if cb.isChecked()]
                ids += self._extra_pages
                out[spec.name] = ids or None
            else:
                text = w.text().strip()  # type: ignore[attr-defined]
                if k in (M.OPT_PATH, M.OPT_TEXT):
                    text = text or None  # type: ignore[assignment]
                if k == M.AUTO_INT:
                    text = int(text) if text.isdigit() else (text or "auto")  # type: ignore[assignment]
                out[spec.name] = text
        return out

    def set_values(self, values: dict[str, Any]) -> None:
        """Fill the form; fields absent from `values` get their Config default."""
        self._loading = True
        try:
            merged = {**M.default_values(), **values}
            for spec in self.specs:
                self._set(spec, self.editors[spec.name], merged[spec.name])
        finally:
            self._loading = False
        self.changed.emit()

    def _set(self, spec: M.FieldSpec, w: QWidget, v: Any) -> None:
        k = spec.kind
        if k == M.BOOL:
            w.setChecked(bool(v))  # type: ignore[attr-defined]
        elif k in (M.CHOICE, M.OPT_CHOICE):
            i = w.findData(v)  # type: ignore[attr-defined]
            w.setCurrentIndex(max(i, 0))  # type: ignore[attr-defined]
        elif k == M.THEME:
            i = w.findData(v)  # type: ignore[attr-defined]
            if i < 0:  # legacy / unknown name: keep it, renders as minimal
                w.addItem(str(v), v)  # type: ignore[attr-defined]
                i = w.findData(v)  # type: ignore[attr-defined]
            w.setCurrentIndex(i)  # type: ignore[attr-defined]
        elif k in (M.COLOR, M.FONT):
            w.set_value(v)  # type: ignore[attr-defined]
        elif k == M.INT:
            w.setValue(int(v))  # type: ignore[attr-defined]
        elif k == M.FLOAT:
            w.setValue(float(v))  # type: ignore[attr-defined]
        elif k == M.MULTI_CHOICE:
            for cb in w.findChildren(QCheckBox):
                cb.setChecked(cb.text() in (v or []))
        elif k == M.TEXT_LIST:
            w.setPlainText("\n".join(v or []))  # type: ignore[attr-defined]
        elif k == M.PAGES:
            ids = list(v or [])
            self._extra_pages = [i for i in ids if i not in self.page_boxes]
            for pid, cb in self.page_boxes.items():
                cb.setChecked(pid in ids)
        elif k == M.INT_LIST:
            w.setText(_join_ints(v))  # type: ignore[attr-defined]
        elif k in (M.OPT_PATH, M.OPT_TEXT):
            w.setText("" if v is None else str(v))  # type: ignore[attr-defined]
        else:
            w.setText(str(v))  # type: ignore[attr-defined]

    # --- Config / files ---
    def config(self) -> tuple[Config | None, str]:
        """Validate the current values with Config; shows the error text under the form."""
        cfg, msg = M.build_config(self.values())
        self.error_label.setText(msg)
        return cfg, msg

    def load_file(self, path: Path | str) -> None:
        """Load a YAML file into the form (raises ConfigFileError if unreadable)."""
        self.set_values(M.load_values(path))

    def save_file(self, path: Path | str) -> str:
        """Save the current settings as YAML. Returns "" or the validation error (nothing saved)."""
        cfg, msg = self.config()
        if cfg is None:
            return msg
        M.save_yaml(cfg, path)
        return ""
