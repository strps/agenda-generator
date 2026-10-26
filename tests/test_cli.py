import subprocess
import sys
from pathlib import Path

import pytest
from pypdf import PdfReader
from typer.testing import CliRunner

from agenda import cli
from agenda.cli import app, build_overrides, main, split_csv

runner = CliRunner()
EXAMPLE_PAGES = "cover,personal_info,monthly,weekly,habits,health,qr"


@pytest.fixture
def captured(monkeypatch, tmp_path):
    """Replace the exporter so a CLI call only records the validated Config."""
    seen = {}

    def fake(cfg, path):
        seen["cfg"], seen["path"] = cfg, path
        return Path(path)

    monkeypatch.setattr(cli, "export_agenda", fake)
    return seen


def test_split_csv():
    assert split_csv(None) is None
    assert split_csv(" a, b,,c ") == ["a", "b", "c"]


def test_build_overrides_drops_unset_flags():
    assert build_overrides(year=None, theme=None) == {}
    assert build_overrides(year=2027, imposition=False) == {"year": 2027, "imposition": False}


def test_build_overrides_lists_and_numbers():
    out = build_overrides(planners="weekly", qr_url=["a", "b"], num_booklets="3")
    assert out == {"planners": ["weekly"], "qr_urls": ["a", "b"], "num_booklets": 3}
    assert build_overrides(num_booklets="auto") == {"num_booklets": "auto"}


def test_build_overrides_pages_and_category_merge_without_duplicates():
    out = build_overrides(pages="notes,cover", category="core")
    assert out["pages"][:2] == ["notes", "cover"]
    assert len(out["pages"]) == len(set(out["pages"]))
    assert "back_cover" in out["pages"]


def test_build_overrides_unknown_category():
    with pytest.raises(ValueError, match="unknown category"):
        build_overrides(category="nope")


def test_example_defaults(captured):
    assert runner.invoke(app, []).exit_code == 0
    cfg = captured["cfg"]
    assert cfg.page_size == "half_letter" and cfg.booklet_size == 5 and cfg.pages is None
    assert captured["path"] == cli.DEFAULT_OUTPUT


def test_example_custom_selection(captured):
    args = ["--pages", EXAMPLE_PAGES, "--size", "a5", "--booklet", "8", "--unit", "sheets"]
    assert runner.invoke(app, [*args, "--year", "2027"]).exit_code == 0
    cfg = captured["cfg"]
    assert cfg.pages == EXAMPLE_PAGES.split(",")
    assert (cfg.page_size, cfg.booklet_size, cfg.booklet_unit, cfg.year) == (
        "a5",
        8,
        "sheets",
        2027,
    )


def test_example_category(captured):
    assert runner.invoke(app, ["--category", "core,optional"]).exit_code == 0
    from agenda.catalog import pages_by_category

    want = [p.id for c in ("core", "optional") for p in pages_by_category(c)]
    assert captured["cfg"].pages == want


def test_example_imposition_crop_marks(captured):
    assert runner.invoke(app, ["--imposition", "--crop-marks"]).exit_code == 0
    assert captured["cfg"].imposition and captured["cfg"].crop_marks


def test_every_config_field_has_a_flag():
    import typer.main

    from agenda.config import Config

    names = {p.name for p in typer.main.get_command(app).params}
    assert set(Config.model_fields) - {"qr_urls"} <= names  # qr_urls is the repeatable --qr-url


def test_flag_toggles(captured):
    assert (
        runner.invoke(
            app, ["--flat", "--no-page-numbers", "--qr-url", "x", "--qr-url", "y"]
        ).exit_code
        == 0
    )
    cfg = captured["cfg"]
    assert cfg.booklet_folded is False and cfg.page_numbers is False and cfg.qr_urls == ["x", "y"]


@pytest.mark.parametrize(
    "args, text",
    [
        (["--imposition", "--flat"], "imposition requires"),
        (["--booklet-unit", "pages", "--booklet-size", "6"], "multiple of 4"),
        (["--page-size", "bogus"], "bogus"),
        (["--category", "nope"], "unknown category"),
    ],
)
def test_config_rules_come_from_the_model(captured, args, text):
    result = runner.invoke(app, args)
    assert result.exit_code == 2 and text in result.output
    assert "cfg" not in captured


def test_main_returns_codes(tmp_path):
    assert main(["--version"]) == 0
    assert main(["--bogus-flag"]) != 0


def test_end_to_end_subprocess(tmp_path):
    out = tmp_path / "e2e.pdf"
    cmd = [sys.executable, "-m", "agenda", "--pages", "cover,notes", "--size", "a5", "-o", str(out)]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert len(PdfReader(out).pages) > 2


def test_example_list(captured):
    result = runner.invoke(app, ["--list"])
    assert result.exit_code == 0
    assert "cover" in result.output and "VALUE" in result.output
    assert "cfg" not in captured


def test_list_ignores_other_args_and_does_not_render(captured, tmp_path):
    result = runner.invoke(app, ["--list", "--size", "bogus", "-o", str(tmp_path / "x.pdf")])
    assert result.exit_code == 0 and not (tmp_path / "x.pdf").exists()


def test_dry_run_prints_summary_without_rendering(captured, tmp_path):
    out = tmp_path / "x.pdf"
    res = runner.invoke(app, ["--dry-run", "--preset", "essential", "-o", str(out)])
    assert res.exit_code == 0, res.output
    assert "Pages:" in res.output and "wrote" not in res.output
    assert "cfg" not in captured and not out.exists()


def test_dry_run_with_pages_matches_plan(captured):
    res = runner.invoke(app, ["--dry-run", "--pages", EXAMPLE_PAGES, "--booklet", "5"])
    assert res.exit_code == 0, res.output
    assert "Pages:" in res.output


def test_dry_run_with_config_and_override(captured, tmp_path):
    y = tmp_path / "c.yaml"
    y.write_text("preset: essential\nbooklet:\n  size: 4\n  unit: sheets\n")
    base = runner.invoke(app, ["--dry-run", "--config", str(y)])
    over = runner.invoke(app, ["--dry-run", "--config", str(y), "--pages", "cover,qr"])
    assert base.exit_code == over.exit_code == 0
    assert base.output != over.output and "cfg" not in captured


def test_dry_run_needs_no_fonts_and_still_validates(monkeypatch):
    monkeypatch.setattr(cli, "export_agenda", lambda *a: pytest.fail("rendered"))
    assert runner.invoke(app, ["--dry-run", "--year", "1800"]).exit_code == 2


def test_sample_config_yaml_is_valid_and_dry_runs(captured):
    from agenda.config import Config
    from agenda.configfile import load_yaml

    path = Path(__file__).resolve().parent.parent / "config.yaml"
    cfg = Config(**load_yaml(path))
    assert cfg.year == 2027 and cfg.pages[0] == "cover"
    res = runner.invoke(app, ["--dry-run", "--config", str(path)])
    assert res.exit_code == 0, res.output
    assert "cfg" not in captured


def test_page_range_flag(tmp_path, capsys):
    base = ["--year", "2026", "--planners", "weekly", "--daily-months", ""]
    out = tmp_path / "r.pdf"
    assert main([*base, "--page-range", "2-3", "--output", str(out)]) == 0
    assert len(PdfReader(str(out)).pages) == 2
    assert (
        main([*base, "--page-range", "2-3", "--imposition", "--folded", "--output", str(out)]) == 2
    )
    assert "page range" in capsys.readouterr().err
    assert main([*base, "--page-range", "999", "--output", str(out)]) == 2
