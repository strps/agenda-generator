from pathlib import Path

import pytest
from typer.testing import CliRunner

from agenda import cli
from agenda.cli import app
from agenda.configfile import ConfigFileError, flatten, load_yaml, merge

runner = CliRunner()

SAMPLE = """\
page_size: half_letter
booklet:
  size: 5
  unit: sheets
  folded: true
year: 2027
week_start: monday
holiday_country: CR
planners: [weekly, daily]
notes_pattern: dotted
pad_with: notes
pages: [cover, personal_info, yearly, monthly, weekly, habits, health, qr, notes, contacts, back_cover]
"""


@pytest.fixture
def captured(monkeypatch):
    seen = {}

    def fake(cfg, path):
        seen["cfg"], seen["path"] = cfg, path
        return Path(path)

    monkeypatch.setattr(cli, "export_agenda", fake)
    return seen


def write(tmp_path, text, name="c.yaml"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return p


def test_flatten_booklet_block():
    out = flatten({"year": 2027, "booklet": {"size": 8, "unit": "pages", "folded": False}})
    assert out == {
        "year": 2027,
        "booklet_size": 8,
        "booklet_unit": "pages",
        "booklet_folded": False,
    }


def test_flatten_rejects_bad_booklet():
    with pytest.raises(ConfigFileError, match=r"booklet\.colour"):
        flatten({"booklet": {"colour": 1}})
    with pytest.raises(ConfigFileError, match="mapping"):
        flatten({"booklet": 5})
    with pytest.raises(ConfigFileError, match="both set"):
        flatten({"booklet": {"size": 5}, "booklet_size": 6})


def test_merge_overrides_win():
    assert merge({"a": 1, "b": 2}, {"b": 3}) == {"a": 1, "b": 3}


def test_load_yaml_errors(tmp_path):
    assert load_yaml(write(tmp_path, "")) == {}
    with pytest.raises(ConfigFileError, match="top level"):
        load_yaml(write(tmp_path, "- a\n- b\n"))
    with pytest.raises(ConfigFileError, match="invalid YAML"):
        load_yaml(write(tmp_path, "a: [1\n"))
    with pytest.raises(ConfigFileError, match="cannot read"):
        load_yaml(tmp_path / "missing.yaml")


def test_cli_loads_plan_example(captured, tmp_path):
    res = runner.invoke(app, ["--config", str(write(tmp_path, SAMPLE))])
    assert res.exit_code == 0, res.output
    cfg = captured["cfg"]
    assert (cfg.year, cfg.booklet_size, cfg.booklet_unit, cfg.booklet_folded) == (
        2027,
        5,
        "sheets",
        True,
    )
    assert cfg.pages[0] == "cover" and cfg.pages[-1] == "back_cover"


def test_cli_flags_override_yaml(captured, tmp_path):
    cfg_file = write(tmp_path, SAMPLE)
    args = ["--config", str(cfg_file), "--year", "2030", "--booklet", "8", "--pages", "cover,notes"]
    assert runner.invoke(app, args).exit_code == 0
    cfg = captured["cfg"]
    assert (cfg.year, cfg.booklet_size, cfg.pages) == (2030, 8, ["cover", "notes"])
    assert cfg.booklet_unit == "sheets" and cfg.pad_with == "notes"  # still from YAML


def test_false_flag_overrides_yaml_true(captured, tmp_path):
    cfg_file = write(tmp_path, "booklet:\n  folded: true\n")
    assert runner.invoke(app, ["--config", str(cfg_file), "--flat"]).exit_code == 0
    assert captured["cfg"].booklet_folded is False


def test_yaml_output_used_unless_flag(captured, tmp_path):
    cfg_file = write(tmp_path, "output: out/x.pdf\n")
    assert runner.invoke(app, ["--config", str(cfg_file)]).exit_code == 0
    assert captured["path"] == Path("out/x.pdf")
    assert runner.invoke(app, ["--config", str(cfg_file), "-o", "y.pdf"]).exit_code == 0
    assert captured["path"] == Path("y.pdf")


@pytest.mark.parametrize(
    "text, msg",
    [
        ("colour: red\n", "colour"),
        ("booklet:\n  colour: 1\n", "booklet.colour"),
        ("year: 1500\n", "year"),
        ("a: [1\n", "invalid YAML"),
        ("- x\n", "top level"),
    ],
)
def test_yaml_errors_exit_2(captured, tmp_path, text, msg):
    res = runner.invoke(app, ["--config", str(write(tmp_path, text))])
    assert res.exit_code == 2 and msg in res.output and "cfg" not in captured


def test_missing_config_exit_2(captured, tmp_path):
    res = runner.invoke(app, ["--config", str(tmp_path / "nope.yaml")])
    assert res.exit_code == 2 and "cannot read" in res.output


def test_cross_field_rule_sees_merged_values(captured, tmp_path):
    # imposition (flag) + booklet.folded false (YAML): the model rejects the combination once
    cfg_file = write(tmp_path, "booklet:\n  folded: false\n")
    res = runner.invoke(app, ["--config", str(cfg_file), "--imposition"])
    assert res.exit_code == 2 and "imposition" in res.output


def test_flatten_section_block_errors():
    assert flatten({"qr": {"urls": ["a"]}}) == {"qr_urls": ["a"]}
    with pytest.raises(ConfigFileError):
        flatten({"style": {"nope": 1}})
