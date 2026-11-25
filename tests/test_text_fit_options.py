import os
from pathlib import Path

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from agenda import cli, fields, uitext
from agenda.config import Config
from agenda.configfile import load_yaml

ROOT = Path(__file__).resolve().parent.parent


def test_defaults_reproduce_today():
    cfg = Config()
    assert cfg.header_text_fit == "overflow"
    assert cfg.footer_text_fit == "ellipsis"


def test_repo_config_yaml_loads_with_defaults():
    values = load_yaml(ROOT / "config.yaml")
    assert "header_text_fit" not in values and "footer_text_fit" not in values
    cfg = Config(**values)
    assert cfg.header_text_fit == "overflow"
    assert cfg.footer_text_fit == "ellipsis"


def test_cli_accepts_modes(tmp_path):
    out = tmp_path / "a.pdf"
    argv = ["--header-text-fit", "wrap", "--footer-text-fit", "shrink", "--dry-run", "-o", str(out)]
    assert cli.main(argv) == 0


@pytest.mark.parametrize(
    "argv",
    [
        ["--header-text-fit", "bogus"],
        ["--footer-text-fit", "bogus"],
        ["--footer-text-fit", "overflow"],
    ],
)
def test_cli_rejects_invalid(argv, tmp_path):
    assert cli.main([*argv, "--dry-run", "-o", str(tmp_path / "a.pdf")]) == 2


def test_style_block_loads(tmp_path):
    f = tmp_path / "c.yaml"
    f.write_text("style:\n  header_text_fit: shrink\n  footer_text_fit: wrap\n", encoding="utf-8")
    cfg = Config(**load_yaml(f))
    assert cfg.header_text_fit == "shrink" and cfg.footer_text_fit == "wrap"


@pytest.mark.gui
@pytest.mark.parametrize("lang", ["en", "es"])
def test_gui_tooltips(lang):
    from PySide6.QtWidgets import QApplication

    from agenda.gui.settings_panel import SettingsPanel

    QApplication.instance() or QApplication([])
    uitext.set_language(lang)
    try:
        panel = SettingsPanel()
        for n in ("header_text_fit", "footer_text_fit"):
            assert panel.editors[n].toolTip().strip()
            assert fields.detail_help(n).strip()
    finally:
        uitext.set_language("en")
