import os

import pytest
import yaml

from agenda.config import Config
from agenda.gui import settings_model as M


def test_every_config_field_has_a_spec():
    assert [s.name for s in M.field_specs()] == list(Config.model_fields)


def test_kinds_derived_from_annotations():
    k = {s.name: s for s in M.field_specs()}
    assert k["orientation"].kind == M.CHOICE and k["orientation"].choices == (
        "portrait",
        "landscape",
    )
    assert k["preset"].kind == M.OPT_CHOICE and "premium" in k["preset"].choices
    assert k["num_booklets"].kind == M.AUTO_INT
    assert k["planners"].kind == M.MULTI_CHOICE and k["planners"].choices == ("weekly", "daily")
    assert k["year"].kind == M.INT and (k["year"].minimum, k["year"].maximum) == (1900, 2200)
    assert k["inner_margin"].kind == M.FLOAT and k["inner_margin"].minimum == 0
    assert k["booklet_folded"].kind == M.BOOL
    assert k["qr_urls"].kind == M.TEXT_LIST and k["pages"].kind == M.PAGES


def test_defaults_build_a_valid_config():
    cfg, msg = M.build_config(M.default_values())
    assert cfg is not None and msg == ""


def test_build_config_reports_config_errors():
    cfg, msg = M.build_config({**M.default_values(), "year": 1000})
    assert cfg is None and "year" in msg
    cfg, msg = M.build_config({**M.default_values(), "imposition": True, "booklet_folded": False})
    assert cfg is None and "imposition" in msg


def test_parse_lines():
    assert M.parse_lines(" a \n\n b\n") == ["a", "b"]


def test_yaml_roundtrip(tmp_path):
    cfg, _ = M.build_config({**M.default_values(), "year": 2027, "week_start": "sunday"})
    path = tmp_path / "c.yaml"
    M.save_yaml(cfg, path)
    assert yaml.safe_load(path.read_text())["year"] == 2027
    cfg2, msg = M.build_config(M.load_values(path))
    assert msg == "" and cfg2 == cfg


def test_load_values_flattens_booklet_block_and_keeps_unknown_keys(tmp_path):
    path = tmp_path / "c.yaml"
    path.write_text("booklet: {size: 8, unit: pages, folded: true}\nbogus: 1\n")
    values = M.load_values(path)
    assert values["booklet_size"] == 8 and values["booklet_unit"] == "pages"
    cfg, msg = M.build_config(values)
    assert cfg is None and "bogus" in msg


@pytest.fixture(scope="module")
def qapp():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.mark.gui
def test_panel_defaults_roundtrip_to_default_config(qapp):
    from agenda.gui.settings_panel import SettingsPanel

    panel = SettingsPanel()
    cfg, msg = panel.config()
    assert msg == "" and cfg == Config()
    assert set(panel.editors) == set(Config.model_fields)


@pytest.mark.gui
def test_panel_edit_emits_changed_and_updates_config(qapp):
    from agenda.gui.settings_panel import SettingsPanel

    panel = SettingsPanel()
    hits = []
    panel.changed.connect(lambda: hits.append(1))
    panel.editors["year"].setValue(2030)
    panel.editors["language"].setCurrentIndex(panel.editors["language"].findData("en"))
    assert len(hits) == 2
    cfg, _ = panel.config()
    assert cfg.year == 2030 and cfg.language == "en"


@pytest.mark.gui
def test_panel_shows_config_error_without_own_rules(qapp):
    from agenda.gui.settings_panel import SettingsPanel

    panel = SettingsPanel()
    panel.editors["imposition"].setChecked(True)
    panel.editors["booklet_folded"].setChecked(False)
    cfg, _ = panel.config()
    assert cfg is None and "imposition" in panel.error_label.text()


@pytest.mark.gui
def test_panel_pages_checklist_and_months_text(qapp):
    from agenda.gui.settings_panel import SettingsPanel

    panel = SettingsPanel()
    panel.page_boxes["habits"].setChecked(True)
    panel.editors["daily_months"].setText("1,3,5-6")
    cfg, msg = panel.config()
    assert msg == "" and cfg.pages == ["habits"] and cfg.daily_months == [1, 3, 5, 6]


@pytest.mark.gui
def test_window_open_save_yaml(qapp, tmp_path):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    src = tmp_path / "in.yaml"
    src.write_text("year: 2028\nbooklet: {size: 4}\nqr_urls: [a, b]\nplanners: [daily]\n")
    assert win.load_config(str(src)) == ""
    cfg, _ = win.settings.config()
    assert (cfg.year, cfg.booklet_size, cfg.qr_urls, cfg.planners) == (
        2028,
        4,
        ["a", "b"],
        ["daily"],
    )
    out = tmp_path / "out.yaml"
    assert win.save_config(str(out)) == ""
    assert win.load_config(str(out)) == ""
    assert win.settings.config()[0] == cfg


@pytest.mark.gui
def test_window_open_errors_are_returned(qapp, tmp_path):
    from agenda.gui.app import MainWindow

    win = MainWindow()
    assert "cannot read" in win.load_config(str(tmp_path / "missing.yaml"))
    win.settings.editors["imposition"].setChecked(True)
    win.settings.editors["booklet_folded"].setChecked(False)
    out = tmp_path / "bad.yaml"
    assert win.save_config(str(out)) != "" and not out.exists()
