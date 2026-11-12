"""Settings form generated from the ``Config`` model (field kinds come from ``settings_model``).

Widgets only hold values; ``Config`` validates them (``config()`` returns it or an error text).
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from agenda import templates as T
from agenda import themes
from agenda.catalog import catalog_rows, get_page
from agenda.config import Config
from agenda.fields import field_label
from agenda.gui import export_model as EM
from agenda.gui import help_text
from agenda.gui import settings_model as M
from agenda.gui import template_model as TM
from agenda.gui.collapsible import CollapsibleSection
from agenda.gui.hover_tooltip import ExpandingToolTip
from agenda.gui.style_editors import ColorEdit, FileEdit, FontEdit
from agenda.gui.style_model import SPACING
from agenda.uitext import tr

_BIG = 10**9
SECTION_SWITCHED = ("planners", "pages")  # set by the section boxes, not edited directly


def _join_ints(v: Any) -> str:
    return ",".join(str(i) for i in v) if isinstance(v, list) else str(v)


class SettingsPanel(QFrame):
    """Tab list (Whole agenda, then one tab per template) beside the settings of the current tab.

    `changed` fires on any edit; `editors` maps field name -> widget; `tab_changed` gives the key
    of the newly shown tab (GLOBAL or a template key)."""

    changed = Signal()
    section_activated = Signal(str)
    tab_changed = Signal(str)

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

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        self.tab_list = QListWidget()
        self.tab_list.setObjectName("tab_list")
        self.tab_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(self.tab_list)
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)
        self.tab_stack = QStackedWidget()
        right.addWidget(self.tab_stack, 1)
        outer.addLayout(right, 1)

        self.sections: dict[str, CollapsibleSection] = {}
        for sp in T.SECTIONS:
            sec = CollapsibleSection(sp.key, T.section_label(sp.key), sp.enable)
            self.sections[sp.key] = sec
            sec.expanded_changed.connect(lambda on, k=sp.key: on and self.activate(k))
            sec.enable_toggled.connect(lambda on, k=sp.key: self._section_toggled(k, on))
            sec.pressed.connect(lambda k=sp.key: self.activate(k, expand=False))
        self.tab_pages: dict[str, QScrollArea] = {}
        self.tab_items: dict[str, QListWidgetItem] = {}
        self._header_items: list[QListWidgetItem] = []
        self.current_tab = T.GLOBAL
        self.active_section = T.GLOBAL
        self._build_tab(T.GLOBAL, tr("tabs.whole"), T.WHOLE_SECTIONS)
        self.tab_items[T.GLOBAL].setToolTip(tr("tabs.whole_tip"))
        for group, keys in T.tab_groups():
            header = QListWidgetItem(T.group_label(group).upper())
            header.setFlags(Qt.ItemFlag.NoItemFlags)
            font = header.font()
            font.setBold(True)
            font.setPointSizeF(font.pointSizeF() * 0.85)
            header.setFont(font)
            self.tab_list.addItem(header)
            self._header_items.append(header)
            for key in keys:
                self._build_tab(key, T.section_label(key), (key,))
        self.sections[T.GLOBAL].set_expanded(True)
        for key in (T.GLOBAL, T.PADDING, T.MONTH_START, T.MONTH_END, T.STYLING):
            self.sections[key].toggle_button.setToolTip(help_text.TOOLTIPS[f"{key}_section"])
        shown: set[str] = set()  # sections with at least one visible field
        for spec in self.specs:
            w = self._make(spec)
            self.editors[spec.name] = w
            short = help_text.PARAM_SHORT[spec.name]
            detail = help_text.PARAM_DETAILS[spec.name]
            self.tooltips[spec.name] = ExpandingToolTip(w, short, detail)
            form = self.sections[T.group_of(spec.name)].form
            if spec.kind in (M.PAGES, M.PAGE_LIST):
                form.addRow(w)
            else:
                label = QLabel(field_label(spec.name))
                label.setObjectName(f"label_{spec.name}")
                self.label_tooltips[spec.name] = ExpandingToolTip(label, short, detail)
                form.addRow(label, w)
            if spec.name in EM.export_field_names() or spec.name in SECTION_SWITCHED:
                # edited in the export dialog or by section boxes; widgets stay (hidden) so
                # values() round-trips
                form.setRowVisible(w, False)
            else:
                shown.add(T.group_of(spec.name))
        for key in T.TEMPLATE_KEYS:  # alone in its tab: no arrow, the settings always open
            self.sections[key].set_static(key in shown)
            if key not in shown:
                hint = QLabel(tr("settings.no_options"))
                hint.setObjectName("tab_hint")
                hint.setWordWrap(True)
                self.tab_pages[key].widget().layout().insertWidget(1, hint)
        for key in T.WHOLE_SECTIONS:
            if key not in shown:
                self.sections[key].set_static(False)
        self.tab_list.setCurrentItem(self.tab_items[T.GLOBAL])
        self.tab_list.currentItemChanged.connect(self._tab_item_changed)
        width = self.tab_list.sizeHintForColumn(0) + 2 * self.tab_list.frameWidth()
        self.tab_list.setFixedWidth(width + self.tab_list.verticalScrollBar().sizeHint().width())
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setObjectName("settings_error")
        right.addWidget(self.error_label)
        self.changed.connect(self._sync_boxes)
        self.changed.connect(self._refresh_swatches)
        self.changed.connect(self._refresh_pad_uses)
        app = QApplication.instance()
        if app is not None:
            app.focusChanged.connect(lambda _old, new: self.notify_focus(new))
        self.set_values(M.default_values())

    def _build_tab(self, tab: str, title: str, keys: tuple[str, ...]) -> None:
        """A tab-list item and a scrollable settings page holding sections ``keys``."""
        item = QListWidgetItem(title)
        item.setData(Qt.ItemDataRole.UserRole, tab)
        self.tab_list.addItem(item)
        self.tab_items[tab] = item
        body = QWidget()
        col = QVBoxLayout(body)
        gap = SPACING["gap"]
        col.setSpacing(gap)
        col.setContentsMargins(gap, gap, gap, gap)
        for key in keys:
            col.addWidget(self.sections[key])
        col.addStretch(1)
        scroll = QScrollArea()
        scroll.setObjectName(f"tab_{tab}")
        scroll.setWidgetResizable(True)
        scroll.setWidget(body)
        self.tab_stack.addWidget(scroll)
        self.tab_pages[tab] = scroll

    # --- tabs and sections ---
    def show_tab(self, tab: str) -> None:
        """Show tab ``tab`` (GLOBAL or a template key) and select it in the tab list."""
        if tab not in self.tab_pages:
            raise KeyError(f"unknown tab {tab!r}")
        self.tab_list.blockSignals(True)
        self.tab_list.setCurrentItem(self.tab_items[tab])
        self.tab_list.blockSignals(False)
        self.tab_stack.setCurrentWidget(self.tab_pages[tab])
        if tab != self.current_tab:
            self.current_tab = tab
            self.tab_changed.emit(tab)

    def _tab_item_changed(self, item: QListWidgetItem | None, _prev: object = None) -> None:
        tab = item.data(Qt.ItemDataRole.UserRole) if item is not None else None
        if tab:
            self.activate(tab, expand=False)

    def activate(self, key: str, expand: bool = True) -> None:
        """Show the tab of section ``key``; inside the Whole agenda tab, open the section too."""
        sec = self.sections[key]
        self.show_tab(T.tab_of(key))
        if expand and sec.collapsible and not sec.is_expanded():
            sec.set_expanded(True)  # its expanded_changed handler re-enters and emits
            return
        self.active_section = key
        self.section_activated.emit(key)

    def notify_focus(self, widget: QWidget | None) -> None:
        w = widget
        while w is not None:
            if isinstance(w, CollapsibleSection) and self.sections.get(w.key) is w:
                # header focus (a click on the toggle) must not expand: the click itself toggles
                self.activate(w.key, expand=w.body.isAncestorOf(widget))
                return
            w = w.parentWidget()

    def refresh_tab_states(self) -> None:
        """Dim the tabs of templates left out of the agenda, and the group headers."""
        pal = self.tab_list.palette()
        text, base = pal.color(QPalette.ColorRole.Text), pal.color(QPalette.ColorRole.Base)
        muted = QColor(
            (text.red() + base.red()) // 2,
            (text.green() + base.green()) // 2,
            (text.blue() + base.blue()) // 2,
        )
        for item in self._header_items:
            item.setForeground(QBrush(muted))
        for key in T.TEMPLATE_KEYS:
            sec = self.sections[key]
            on = sec.enabled_state()
            item = self.tab_items[key]
            item.setForeground(QBrush(text if on else muted))
            font = item.font()
            font.setItalic(not on)
            item.setFont(font)
            label = T.section_label(key)
            item.setToolTip("" if on else tr("app.template_disabled", label=label))

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
        self.refresh_tab_states()

    def _refresh_swatches(self) -> None:
        palette = themes.palette_for(self.values()["theme"])
        for spec in self.specs:
            if spec.kind == M.COLOR:
                w = self.editors[spec.name]
                w.set_fallback(palette[spec.name.removeprefix("color_")])  # type: ignore[attr-defined]

    def _refresh_pad_uses(self) -> None:
        """Badge, ring and tooltip of the sections whose page is used as padding or filler."""
        roles = TM.pad_roles(self.values())
        for key, sec in self.sections.items():
            if T.section(key).page_id is None:
                continue
            fields = roles.get(key, [])
            sec.set_pad_use(TM.pad_label(fields))
            sec.toggle_button.setToolTip(TM.header_tooltip(key, fields))
            if sec.enable_box is not None:
                note = TM.pad_text(fields)
                sec.enable_box.setToolTip(tr("section.include_tip") + (f"\n{note}" if note else ""))

    # --- widget factory ---
    def _make(self, spec: M.FieldSpec) -> QWidget:
        k = spec.kind
        if k == M.BOOL:
            w: QWidget = QCheckBox()
            w.toggled.connect(self._edited)
        elif k in (M.CHOICE, M.OPT_CHOICE):
            w = QComboBox()
            if k == M.OPT_CHOICE:
                w.addItem(tr("settings.none"), None)
            for c in spec.choices:
                w.addItem(c, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.THEME:
            w = QComboBox()
            for c in spec.choices:
                w.addItem(c, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.PAGE_CHOICE:
            w = QComboBox()
            for c in spec.choices:
                self._add_page_item(w, c)
            w.currentIndexChanged.connect(self._edited)
        elif k == M.COLOR:
            w = ColorEdit()
            w.edited.connect(self._edited)
        elif k == M.FONT:
            w = FontEdit()
            w.edited.connect(self._edited)
        elif k == M.OPT_PATH:
            w = FileEdit()
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
            w.setPlaceholderText(tr("settings.one_per_line"))
            w.setFixedHeight(60)
            w.textChanged.connect(self._edited)
        elif k == M.PAGES:
            w = self._make_pages()
        elif k == M.PAGE_LIST:
            w = QWidget()  # bare column of checkboxes: no frame or title, the section names it
            w.setObjectName("page_list")
            lay = QVBoxLayout(w)
            lay.setContentsMargins(0, 0, 0, 0)
            for c in spec.choices:
                cb = QCheckBox(get_page(c).name)
                cb.setProperty("page_id", c)
                cb.setToolTip(TM.page_text(c))
                cb.toggled.connect(self._edited)
                lay.addWidget(cb)
        else:  # text, path, int_list, auto_int: edited as text, parsed by Config
            w = QLineEdit()
            w.textEdited.connect(self._edited)
        return w

    @staticmethod
    def _add_page_item(w: QComboBox, value: str) -> None:
        """One page-select item: the page name (or filler mode), its id, a tooltip."""
        try:
            text = f"{get_page(value).name} ({value})"
            tip = TM.choice_tooltip(value)
        except KeyError:  # filler mode, or an unknown id kept so Config reports it
            text, tip = value, TM.FILLER_TEXT.get(value, "")
        w.addItem(text, value)
        w.setItemData(w.count() - 1, tip, Qt.ItemDataRole.ToolTipRole)

    def _make_pages(self) -> QGroupBox:
        box = QGroupBox(tr("settings.pages_title"))
        lay = QVBoxLayout(box)
        category = None
        for row in catalog_rows():
            if row["category"] != category:
                category = row["category"]
                lay.addWidget(QLabel(tr("settings.category", category=category)))
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
            elif k in (M.CHOICE, M.OPT_CHOICE, M.THEME, M.PAGE_CHOICE):
                out[spec.name] = w.currentData()  # type: ignore[attr-defined]
            elif k in (M.COLOR, M.FONT, M.OPT_PATH) or k in (M.INT, M.FLOAT):
                out[spec.name] = w.value()  # type: ignore[attr-defined]
            elif k == M.MULTI_CHOICE:
                out[spec.name] = [
                    cb.text()
                    for cb in w.findChildren(QCheckBox)
                    if cb.isChecked()  # type: ignore[attr-defined]
                ]
            elif k == M.PAGE_LIST:
                out[spec.name] = [
                    cb.property("page_id") for cb in w.findChildren(QCheckBox) if cb.isChecked()
                ]
            elif k == M.TEXT_LIST:
                out[spec.name] = M.parse_lines(w.toPlainText())  # type: ignore[attr-defined]
            elif k == M.PAGES:
                ids = [i for i, cb in self.page_boxes.items() if cb.isChecked()]
                ids += self._extra_pages
                out[spec.name] = ids or None
            else:
                text = w.text().strip()  # type: ignore[attr-defined]
                if k == M.OPT_TEXT:
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
        elif k == M.PAGE_CHOICE:
            v = str(v).strip()
            if v.lower() in TM.FILLER_TEXT:  # Config lower-cases the filler modes
                v = v.lower()
            if w.findData(v) < 0:  # type: ignore[attr-defined]
                self._add_page_item(w, v)  # type: ignore[arg-type]
            w.setCurrentIndex(w.findData(v))  # type: ignore[attr-defined]
        elif k == M.THEME:
            i = w.findData(v)  # type: ignore[attr-defined]
            if i < 0:  # legacy / unknown name: keep it, renders as minimal
                w.addItem(str(v), v)  # type: ignore[attr-defined]
                i = w.findData(v)  # type: ignore[attr-defined]
            w.setCurrentIndex(i)  # type: ignore[attr-defined]
        elif k in (M.COLOR, M.FONT, M.OPT_PATH):
            w.set_value(v)  # type: ignore[attr-defined]
        elif k == M.INT:
            w.setValue(int(v))  # type: ignore[attr-defined]
        elif k == M.FLOAT:
            w.setValue(float(v))  # type: ignore[attr-defined]
        elif k == M.MULTI_CHOICE:
            for cb in w.findChildren(QCheckBox):
                cb.setChecked(cb.text() in (v or []))
        elif k == M.PAGE_LIST:
            for cb in w.findChildren(QCheckBox):
                cb.setChecked(cb.property("page_id") in (v or []))
        elif k == M.TEXT_LIST:
            w.setPlainText("\n".join(v or []))  # type: ignore[attr-defined]
        elif k == M.PAGES:
            ids = list(v or [])
            self._extra_pages = [i for i in ids if i not in self.page_boxes]
            for pid, cb in self.page_boxes.items():
                cb.setChecked(pid in ids)
        elif k == M.INT_LIST:
            w.setText(_join_ints(v))  # type: ignore[attr-defined]
        elif k == M.OPT_TEXT:
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
