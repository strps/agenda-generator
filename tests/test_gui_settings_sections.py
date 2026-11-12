import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QCheckBox, QLabel

from agenda import templates as T
from agenda.catalog import preset_pages
from agenda.config import Config
from agenda.gui import export_model as EM
from agenda.gui import settings_model as M
from agenda.gui.collapsible import CollapsibleSection
from agenda.gui.settings_panel import SECTION_SWITCHED, SettingsPanel

pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp):
    return SettingsPanel()


def _section_of(w):
    while w is not None and not isinstance(w, CollapsibleSection):
        w = w.parentWidget()
    return w


def test_sections_in_order(panel):
    assert list(panel.sections) == [s.key for s in T.SECTIONS]
    for s in T.SECTIONS:
        assert panel.sections[s.key].toggle_button.text().replace("&&", "&").endswith(s.label)
    assert panel.sections[T.GLOBAL].is_expanded()
    assert not panel.sections[T.PADDING].is_expanded()
    daily = panel.sections["daily"]
    assert daily.body.isVisibleTo(daily) and not daily.toggle_button.text().startswith("▸")


def test_editor_placement(panel):
    for name, w in panel.editors.items():
        assert _section_of(w).key == T.group_of(name)


def test_default_boxes(panel):
    for k in ("daily", "weekly", "contacts"):
        assert panel.sections[k].enable_box.isChecked()
    for k in ("qr", "schedule", "habits", "niche_entrepreneur", "niche_student", "niche_fitness"):
        assert not panel.sections[k].enable_box.isChecked()
    for k in (T.GLOBAL, T.PADDING, T.STYLING):
        assert panel.sections[k].enable_box is None
    assert panel.sections["notes"].enable_box.isChecked()
    assert not panel.editors["qr_urls"].isEnabled()
    assert not panel.editors["habits_max"].isEnabled()
    for n in ("extra_padding", "pad_with"):
        assert _section_of(panel.editors[n]).key == T.PADDING
        assert panel.editors[n].isEnabled()


def test_contacts_box(panel):
    box = panel.sections["contacts"].enable_box
    box.setChecked(False)
    assert panel.editors["contacts_pages"].value() == 0
    assert not panel.editors["contacts_pages"].isEnabled()
    box.setChecked(True)
    assert panel.editors["contacts_pages"].value() == 1


def test_daily_box_syncs_planners(panel):
    hits = []
    panel.changed.connect(lambda: hits.append(1))
    box = panel.sections["daily"].enable_box
    box.setChecked(False)
    assert panel.config()[0].planners == ["weekly"]
    assert len(hits) == 1
    assert not panel.editors["daily_months"].isEnabled()
    cb = {c.text(): c for c in panel.editors["planners"].findChildren(QCheckBox)}["daily"]
    assert not cb.isChecked()
    cb.setChecked(True)
    assert box.isChecked() and panel.editors["daily_months"].isEnabled()


def test_qr_box_with_preset(panel):
    panel.set_values({**M.default_values(), "preset": "essential", "qr_urls": ["https://x.org"]})
    panel.sections["qr"].enable_box.setChecked(True)
    cfg, msg = panel.config()
    assert cfg is not None, msg
    assert set(cfg.pages) == set(preset_pages("essential")) | {"qr"}
    assert panel.page_boxes["qr"].isChecked()


def test_activation(panel):
    seen, tabs = [], []
    panel.section_activated.connect(seen.append)
    panel.tab_changed.connect(tabs.append)
    panel.activate("daily")
    assert seen == ["daily"] and panel.active_section == "daily"
    assert tabs == ["daily"] and panel.current_tab == "daily"
    seen.clear()
    panel.sections[T.PADDING].set_expanded(True)
    assert seen == [T.PADDING] and panel.current_tab == T.GLOBAL
    seen.clear()
    panel.notify_focus(panel.editors["qr_urls"])
    assert seen == ["qr"]
    seen.clear()
    panel.notify_focus(None)
    panel.notify_focus(QLabel("x"))
    assert seen == []


def test_tab_list(panel):
    items = [panel.tab_list.item(i) for i in range(panel.tab_list.count())]
    keys = [it.data(Qt.ItemDataRole.UserRole) for it in items]
    assert keys[0] == T.GLOBAL and items[0].text() == "Whole agenda"
    assert [k for k in keys if k] == [T.GLOBAL, *(k for _, ks in T.tab_groups() for k in ks)]
    headers = [it for it, k in zip(items, keys, strict=True) if not k]
    assert [h.text() for h in headers] == [T.group_label(g).upper() for g, _ in T.tab_groups()]
    assert all(not h.flags() & Qt.ItemFlag.ItemIsSelectable for h in headers)
    assert panel.tab_stack.count() == 1 + len(T.TEMPLATE_KEYS)
    for key in T.WHOLE_SECTIONS:
        assert panel.tab_pages[T.GLOBAL].isAncestorOf(panel.sections[key])
    for key in T.TEMPLATE_KEYS:
        assert panel.tab_pages[key].isAncestorOf(panel.sections[key])


def test_tab_list_click_and_focus(panel):
    seen = []
    panel.section_activated.connect(seen.append)
    panel.tab_list.setCurrentItem(panel.tab_items["todo"])
    assert seen == ["todo"] and panel.tab_stack.currentWidget() is panel.tab_pages["todo"]
    panel.activate(T.STYLING)
    assert panel.tab_list.currentItem() is panel.tab_items[T.GLOBAL]
    assert panel.sections[T.STYLING].is_expanded()
    panel.notify_focus(panel.editors["qr_urls"])
    assert panel.current_tab == "qr" and panel.tab_list.currentItem() is panel.tab_items["qr"]


def test_disabled_tabs_dimmed(panel):
    qr, daily = panel.tab_items["qr"], panel.tab_items["daily"]
    assert qr.font().italic() and qr.toolTip() and not daily.font().italic()
    panel.sections["qr"].enable_box.setChecked(True)
    assert not qr.font().italic() and qr.toolTip() == ""


def test_header_focus_does_not_expand(panel):
    sec = panel.sections[T.PADDING]
    panel.notify_focus(sec.toggle_button)
    assert panel.active_section == T.PADDING and not sec.is_expanded()


def test_set_values_resyncs(panel):
    panel.set_values({**M.default_values(), "planners": ["daily"]})
    assert not panel.sections["weekly"].enable_box.isChecked()
    assert isinstance(panel.config()[0], Config)


def test_page_sections_replace_global_lists(panel):
    for name in ("planners", "pages"):
        assert not panel.editors[name].isVisibleTo(panel.sections[T.GLOBAL])
    sec = panel.sections["budget"]
    assert not sec.collapsible and not sec.toggle_button.isCheckable()
    assert not sec.body.isVisibleTo(sec)
    hint = panel.tab_pages["budget"].findChild(QLabel, "tab_hint")
    assert hint is not None and hint.text()
    assert panel.tab_pages["daily"].findChild(QLabel, "tab_hint") is None
    panel.activate("budget")
    assert panel.active_section == "budget" and panel.current_tab == "budget"
    sec.enable_box.setChecked(True)
    assert "budget" in panel.values()["pages"]
    sec.enable_box.setChecked(False)
    assert "budget" not in (panel.values()["pages"] or [])


def test_open_iff_visible_fields(panel):
    hidden = {*EM.export_field_names(), *SECTION_SWITCHED}
    with_fields = {T.group_of(s.name) for s in panel.specs if s.name not in hidden}
    for key, sec in panel.sections.items():
        if key in T.TEMPLATE_KEYS:  # alone in its tab: settings always open
            assert not sec.collapsible and sec.body.isVisibleTo(sec) == (key in with_fields), key
        else:
            assert sec.collapsible == (key in with_fields), key


def test_page_selects(panel):
    w = panel.editors["pad_with"]
    assert w.currentData() == "notes"
    assert "Notes" in w.currentText()
    assert w.itemData(w.currentIndex(), Qt.ItemDataRole.ToolTipRole)
    f = panel.editors["weekly_filler"]
    assert [f.itemData(i) for i in range(2)] == ["blank", "none"]
    assert f.findData("weekly") < 0  # a spread can't fill a one-page slot
    panel.set_values({"weekly_filler": "todo", "pad_with": "nope"})
    assert f.currentData() == "todo"
    assert w.currentData() == "nope" and panel.config()[0] is None  # kept so Config reports it


def test_pad_use_badges(panel):
    notes = panel.sections["notes"]
    assert notes.pad_label.text() == "padding" and not notes.pad_label.isHidden()
    assert notes.enable_box.property("pad") is True
    assert "Padding: pads the last booklet" in notes.toggle_button.toolTip()
    todo = panel.sections["todo"]
    assert todo.pad_label.isHidden() and not todo.enable_box.property("pad")
    panel.set_values({"weekly_filler": "todo", "daily_filler": "todo", "pad_with": "todo"})
    assert todo.pad_label.text() == "padding · week filler · day filler"
    assert todo.enable_box.property("pad") is True
    assert not todo.enable_box.isChecked()  # used as padding only, the page itself stays off
    assert notes.pad_label.isHidden() and not notes.enable_box.property("pad")
    assert "Week pages" in todo.toggle_button.toolTip()


def test_month_checkboxes(panel):
    boxes = {
        k: {cb.property("page_id"): cb for cb in panel.editors[f].findChildren(QCheckBox)}
        for k, f in ((T.MONTH_START, "month_start_pages"), (T.MONTH_END, "month_end_pages"))
    }
    assert set(boxes[T.MONTH_START]) == {"budget", "habits", "monthly_review", "health", "quotes"}
    assert boxes[T.MONTH_START]["budget"].text() == "Monthly budget"
    boxes[T.MONTH_START]["budget"].setChecked(True)
    boxes[T.MONTH_END]["monthly_review"].setChecked(True)
    v = panel.values()
    assert v["month_start_pages"] == ["budget"] and v["month_end_pages"] == ["monthly_review"]
    budget = panel.sections["budget"]
    assert budget.pad_label.text() == "month start" and budget.enable_box.property("pad")
    assert not budget.enable_box.isChecked()
    assert "Start of each month" in budget.toggle_button.toolTip()
    assert panel.sections["monthly_review"].pad_label.text() == "month end"
    boxes[T.MONTH_END]["budget"].setChecked(True)  # start and end: Config rejects it
    assert panel.config()[0] is None
    panel.set_values({"month_end_pages": ["health"]})
    assert boxes[T.MONTH_END]["health"].isChecked() and not boxes[T.MONTH_END]["budget"].isChecked()
