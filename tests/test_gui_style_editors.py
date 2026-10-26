import os
import shutil

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from agenda import fonts, themes
from agenda import templates as T
from agenda.config import Config
from agenda.gui import settings_model as M
from agenda.gui.hover_tooltip import ExpandingToolTip
from agenda.gui.settings_panel import SettingsPanel

COLORS = [n for n in Config.model_fields if n.startswith("color_")]
FONTS = ["font_primary", "font_secondary"]


pytestmark = pytest.mark.gui


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def panel(qapp):
    return SettingsPanel()


def test_specs_kinds():
    specs = {s.name: s for s in M.field_specs()}
    assert specs["theme"].kind == "theme"
    assert specs["theme"].choices == tuple(themes.THEMES)
    assert len(COLORS) == 7
    assert all(specs[n].kind == "color" for n in COLORS)
    assert all(specs[n].kind == "font" for n in FONTS)


def test_editors_in_styling_section(panel):
    sec = panel.sections[T.STYLING]
    assert "PDF colors && fonts" in sec.toggle_button.text()
    for n in ["theme", *COLORS, *FONTS]:
        w = panel.editors[n]
        assert sec.isAncestorOf(w), n
        assert isinstance(panel.tooltips[n], ExpandingToolTip)
        assert w.toolTip()


def test_color_edit(panel):
    spy = []
    panel.changed.connect(lambda: spy.append(1))
    ed = panel.editors["color_accent"]
    assert panel.values()["color_accent"] is None
    default = themes.rgb_to_hex(themes.THEMES["minimal"]["accent"])
    assert default in ed.swatch.styleSheet()
    ed.set_value("#0000ff")
    assert panel.values()["color_accent"] == "#0000ff"
    assert len(spy) == 1
    assert "#0000ff" in ed.swatch.styleSheet()
    ed.clear_button.click()
    assert panel.values()["color_accent"] is None
    assert default in ed.swatch.styleSheet()
    # theme change refreshes the swatch
    panel.editors["theme"].setCurrentIndex(panel.editors["theme"].findData("ocean"))
    assert themes.rgb_to_hex(themes.THEMES["ocean"]["accent"]) in ed.swatch.styleSheet()


def test_color_dialog_and_invalid(panel, monkeypatch):
    ed = panel.editors["color_ink"]
    monkeypatch.setattr(type(ed), "_pick_color", lambda self, initial: "#112233")
    ed.swatch.click()
    assert panel.values()["color_ink"] == "#112233"
    ed.line.setText("nope")
    ed.line.textEdited.emit("nope")
    cfg, msg = panel.config()
    assert cfg is None and "color_ink" in msg


def test_legacy_theme(panel):
    panel.set_values({"theme": "legacy-name"})
    assert panel.values()["theme"] == "legacy-name"
    assert panel.editors["theme"].findData("legacy-name") >= 0


def test_font_edit(panel, tmp_path, monkeypatch):
    ed = panel.editors["font_primary"]
    assert panel.values()["font_primary"] == "inter"
    ed.set_value("inter")
    assert panel.values()["font_primary"] == "inter"
    f = tmp_path / "MyFont-Regular.ttf"
    shutil.copy(fonts.BUILTIN["inter"][""], f)
    ed.set_value(str(f))
    assert panel.values()["font_primary"] == str(f)
    monkeypatch.setattr(type(ed), "_pick_file", lambda self: "inter")
    ed.browse_button.click()
    assert panel.values()["font_primary"] == "inter"


def test_yaml_round_trip(panel, tmp_path):
    f = tmp_path / "MyFont-Regular.ttf"
    shutil.copy(fonts.BUILTIN["inter"][""], f)
    values = {
        **M.default_values(),
        "theme": "forest",
        "color_accent": "#0000ff",
        "color_holiday_fill": "#eeeeee",
        "font_primary": str(f),
    }
    panel.set_values(values)
    style = ["theme", *COLORS, *FONTS]
    assert {k: panel.values()[k] for k in style} == {k: values[k] for k in style}
    before = M.build_config(panel.values())[0]
    out = tmp_path / "c.yaml"
    assert panel.save_file(out) == ""
    panel.set_values(M.default_values())
    panel.load_file(out)
    assert M.build_config(panel.values())[0] == before
    assert before.color_accent == "#0000ff" and before.theme == "forest"


def test_no_appearance_widget(panel):
    assert not [w for w in panel.findChildren(QWidget) if w.objectName() == "appearance"]
