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
    assert not panel.sections["daily"].is_expanded()


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
    seen = []
    panel.section_activated.connect(seen.append)
    panel.sections["daily"].set_expanded(True)
    assert seen == ["daily"] and panel.active_section == "daily"
    seen.clear()
    panel.notify_focus(panel.editors["qr_urls"])
    assert seen == ["qr"]
    seen.clear()
    panel.notify_focus(None)
    panel.notify_focus(QLabel("x"))
    assert seen == []


def test_active_header(panel):
    def active():
        return [k for k, s in panel.sections.items() if s.toggle_button.property("active")]

    assert active() == [T.GLOBAL]
    panel.notify_focus(panel.editors["qr_urls"])
    assert active() == ["qr"]
    panel.sections["daily"].pressed.emit()
    assert active() == ["daily"] and not panel.sections["daily"].is_expanded()


def test_header_focus_does_not_expand(panel):
    sec = panel.sections["weekly"]
    panel.notify_focus(sec.toggle_button)
    assert panel.active_section == "weekly" and not sec.is_expanded()
    panel.notify_focus(sec.enable_box)
    assert not sec.is_expanded()


def test_set_values_resyncs(panel):
    panel.set_values({**M.default_values(), "planners": ["daily"]})
    assert not panel.sections["weekly"].enable_box.isChecked()
    assert isinstance(panel.config()[0], Config)


def test_page_sections_replace_global_lists(panel):
    for name in ("planners", "pages"):
        assert not panel.editors[name].isVisibleTo(panel.sections[T.GLOBAL])
    sec = panel.sections["budget"]
    assert not sec.collapsible and not sec.toggle_button.isCheckable()
    panel.activate("budget")
    assert panel.active_section == "budget" and not sec.is_expanded()
    sec.enable_box.setChecked(True)
    assert "budget" in panel.values()["pages"]
    sec.enable_box.setChecked(False)
    assert "budget" not in (panel.values()["pages"] or [])


def test_collapsible_iff_visible_fields(panel):
    hidden = {*EM.export_field_names(), *SECTION_SWITCHED}
    with_fields = {T.group_of(s.name) for s in panel.specs if s.name not in hidden}
    for key, sec in panel.sections.items():
        assert sec.collapsible == (key in with_fields), key
    assert not panel.sections["budget"].collapsible and panel.sections["weekly"].collapsible


def test_groups(panel):
    assert list(panel.groups) == [g.key for g in T.GROUPS]
    for g in T.GROUPS:
        group = panel.groups[g.key]
        assert group.is_expanded() == g.expanded
        for key in g.sections:
            assert group.body.isAncestorOf(panel.sections[key])
    group = panel.groups["optional"]
    assert not group.is_expanded()
    panel.activate("todo")  # activating a section inside a closed group opens the group
    assert group.is_expanded() and panel.active_section == "todo"


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
