import pytest
from PySide6.QtWidgets import QApplication

from agenda.gui import export_model as EM
from agenda.gui import settings_model as M
from agenda.gui.export_dialog import ExportDialog
from agenda.gui.hover_tooltip import ExpandingToolTip

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def base():
    return {**M.default_values(), **SMALL}


def test_populates_controls(qapp):
    v = {
        **base(),
        "page_numbers": True,
        "page_number_start": 7,
        "sheet_size": "a4",
        "spreads": True,
        "bleed": 4.5,
        "num_booklets": 3,
        "page_number_format": "{n}/{total}",
    }
    d = ExportDialog(v, 40, open_after=True, page_range="")
    c = d.controls
    assert c["page_numbers"].isChecked()
    assert c["page_number_start"].value() == 7
    assert c["sheet_size"].currentData() == "a4"
    assert c["bleed"].value() == 4.5
    assert c["num_booklets"].text() == "3"
    assert c["page_number_format"].text() == "{n}/{total}"
    assert d.layout_buttons["spreads"].isChecked()
    assert d.open_after()
    assert d.output_edit.text() == "agenda.pdf"


def test_edits_only_export_fields(qapp):
    v = {**base(), "language": "de"}
    d = ExportDialog(v, 40)
    assert d.result_values() == {**v, "output": "agenda.pdf"}
    d.controls["page_numbers"].setChecked(True)
    d.controls["page_number_start"].setValue(5)
    d.controls["page_number_position"].setCurrentIndex(
        d.controls["page_number_position"].findData("center")
    )
    d.output_edit.setText("x.pdf")
    r = d.result_values()
    assert r["page_numbers"] and r["page_number_start"] == 5
    assert r["page_number_position"] == "center" and r["output"] == "x.pdf"
    changed = {k for k in r if r[k] != v[k]}
    assert changed <= set(EM.export_field_names())


def test_booklets_radio(qapp):
    d = ExportDialog({**base(), "booklet_folded": False}, 40)
    assert d.controls["booklet_folded"].isEnabled()
    d.layout_buttons["booklets"].setChecked(True)
    r = d.result_values()
    assert r["imposition"] and r["booklet_folded"] and not r["spreads"]
    assert d.controls["booklet_folded"].isChecked()
    assert not d.controls["booklet_folded"].isEnabled()
    d.layout_buttons["spreads"].setChecked(True)
    r = d.result_values()
    assert r["spreads"] and not r["imposition"]
    assert d.controls["booklet_folded"].isEnabled()


def test_enable_rules(qapp):
    d = ExportDialog(base(), 40)
    assert not d.controls["sheet_size"].isEnabled()
    assert not d.controls["page_number_start"].isEnabled()
    assert d.page_range_edit.isEnabled()
    d.controls["page_numbers"].setChecked(True)
    assert d.controls["page_number_start"].isEnabled()
    d.layout_buttons["spreads"].setChecked(True)
    assert d.controls["sheet_size"].isEnabled()
    assert not d.page_range_edit.isEnabled()


def test_invalid_disables_export(qapp):
    d = ExportDialog(base(), 40)
    assert d.ok_button.isEnabled() and d.error_label.text() == ""
    d.layout_buttons["booklets"].setChecked(True)
    d.page_range_edit.setText("2-3")
    assert not d.ok_button.isEnabled()
    assert "page range" in d.error_label.text()
    d.page_range_edit.setText("")
    assert d.ok_button.isEnabled()
    d.controls["booklet_unit"].setCurrentIndex(d.controls["booklet_unit"].findData("pages"))
    d.controls["booklet_size"].setValue(3)
    assert not d.ok_button.isEnabled()
    assert d.error_label.text()


def test_tooltips(qapp):
    d = ExportDialog(base(), 40)
    assert set(EM.export_field_names()) - {"imposition", "spreads"} <= set(d.controls)
    for name, w in d.controls.items():
        has_expanding = any(isinstance(c, ExpandingToolTip) for c in w.children())
        assert w.toolTip() or has_expanding, name


def test_cli_line_and_getters(qapp):
    d = ExportDialog(base(), 40, page_range="1-2")
    assert d.page_range() == "1-2"
    assert d.cli_line.text().startswith("agenda-gen")
    assert "--page-range 1-2" in d.cli_line.text()
    d.controls["page_numbers"].setChecked(True)
    assert "--page-numbers" in d.cli_line.text()
    d.open_after_box.setChecked(True)
    assert d.open_after()
