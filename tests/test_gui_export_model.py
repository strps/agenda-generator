import subprocess
import sys

import pypdf
import pytest

from agenda.cli import main
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.gui import export_model as EM
from agenda.gui import help_text as HT
from agenda.gui.settings_model import default_values

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


def base():
    return {**default_values(), **SMALL}


def test_no_pyside_import():
    code = "import sys, agenda.gui.export_model; sys.exit('PySide6' in sys.modules)"
    assert subprocess.run([sys.executable, "-c", code], check=False).returncode == 0


def test_fields_exist_and_documented():
    names = EM.export_field_names()
    assert len(names) == len(set(names))
    for n in names:
        assert n in Config.model_fields
        assert n in HT.PARAM_SHORT and n in HT.PARAM_DETAILS


def test_layout_roundtrip():
    v = base()
    assert EM.layout_of(v) == "pages"
    for lay in EM.LAYOUTS:
        w = EM.with_layout(v, lay)
        assert EM.layout_of(w) == lay
        assert w is not v
    b = EM.with_layout({**v, "booklet_folded": False}, "booklets")
    assert (b["imposition"], b["booklet_folded"], b["spreads"]) == (True, True, False)
    s = EM.with_layout(b, "spreads")
    assert (s["imposition"], s["spreads"]) == (False, True)
    with pytest.raises(ValueError):
        EM.with_layout(v, "x")


def test_field_enabled():
    v = base()
    assert not EM.field_enabled(v, "page_number_start")
    assert EM.field_enabled({**v, "page_numbers": True}, "page_number_format")
    assert not EM.field_enabled(v, "sheet_size") and not EM.field_enabled(v, "crop_marks")
    assert EM.field_enabled(v, "page_range") and EM.field_enabled(v, "booklet_folded")
    sp = EM.with_layout(v, "spreads")
    assert EM.field_enabled(sp, "sheet_size") and EM.field_enabled(sp, "crop_marks")
    assert not EM.field_enabled(sp, "bleed")
    assert EM.field_enabled({**sp, "crop_marks": True}, "bleed")
    assert not EM.field_enabled(sp, "page_range")
    assert not EM.field_enabled(EM.with_layout(v, "booklets"), "booklet_folded")


def test_validate():
    v = base()
    assert EM.validate(v, "") == ""
    assert EM.validate(v, "2-3") == ""
    assert "page range" in EM.validate(v, "0")
    assert "page range" in EM.validate(v, "9999")
    assert "page range" in EM.validate(EM.with_layout(v, "booklets"), "2-3")
    assert "booklet_size" in EM.validate({**v, "booklet_size": 3, "booklet_unit": "pages"})
    assert EM.validate({**v, "crop_marks": True}) != ""


def test_cli_args_basic():
    d = default_values()
    assert EM.cli_args(base(), "", d) == []
    v = {**base(), "page_numbers": True, "booklet_folded": False, "debug_grid": True}
    a = EM.cli_args(v, "1-3", d)
    assert "--page-numbers" in a and "--flat" in a and "--debug-grid" in a
    assert a[-2:] == ["--page-range", "1-3"]
    assert EM.cli_args(base(), "all", d) == []
    cmd = EM.cli_command(v, "", d, config_path="my cfg.yaml")
    assert cmd.startswith("agenda-gen --config 'my cfg.yaml'")


def _pages(path):
    return len(pypdf.PdfReader(str(path)).pages)


@pytest.mark.parametrize(
    "layout,extra,rng",
    [
        ("pages", {"page_numbers": True, "page_number_start": 5}, ""),
        ("pages", {}, "2-3"),
        ("spreads", {"sheet_size": "a4", "crop_marks": True}, ""),
        ("booklets", {"booklet_size": 2}, ""),
    ],
)
def test_cli_args_match_export(tmp_path, layout, extra, rng):
    v = EM.with_layout({**base(), **extra}, layout)
    assert EM.validate(v, rng) == ""
    args = EM.cli_args(v, rng, default_values())
    base_args = [
        "--year",
        "2026",
        "--planners",
        "weekly",
        "--daily-months",
        "",
    ]
    out = tmp_path / "cli.pdf"
    assert main(base_args + args + ["--output", str(out)]) == 0
    cfg = Config(**v)
    ref = tmp_path / "ref.pdf"
    pages = None
    if rng:
        from agenda.assembler import build_plan
        from agenda.pagerange import parse_page_range

        pages = parse_page_range(rng, len(build_plan(cfg)))
    export_agenda(cfg, ref, pages=pages) if pages else export_agenda(cfg, ref)
    assert _pages(out) == _pages(ref)
