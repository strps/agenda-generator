import shutil
from pathlib import Path

import pytest
from pypdf import PdfReader

from agenda import fonts
from agenda.cli import main
from agenda.config import Config
from agenda.exporter import export_agenda

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}
ROOT = Path(__file__).resolve().parent.parent
INTER = ROOT / "assets" / "fonts"


def _base_fonts(reader):
    names = set()
    for page in reader.pages:
        for f in page["/Resources"].get("/Font", {}).values():
            names.add(str(f.get_object()["/BaseFont"]))
    return names


def _copy(tmp_path, styles=("Regular", "Bold")):
    for s in styles:
        shutil.copy(INTER / f"Inter-{s}.ttf", tmp_path / f"MyFont-{s}.ttf")
    return tmp_path / "MyFont-Regular.ttf"


def test_default_embeds_only_inter(tmp_path):
    reader = PdfReader(str(export_agenda(Config(**SMALL), tmp_path / "a.pdf")))
    assert _base_fonts(reader)
    assert all("Inter" in n for n in _base_fonts(reader))


def test_resolve_builtin_and_siblings(tmp_path):
    files = fonts.resolve("Inter")
    assert set(files) == {"", "B", "I", "BI"} and all(p.is_file() for p in files.values())
    reg = _copy(tmp_path, ("Regular", "Bold"))
    got = fonts.resolve(str(reg))
    assert got["B"].name == "MyFont-Bold.ttf"
    assert got["I"] == reg and got["BI"] == reg
    for bad in ("nope", str(tmp_path / "missing.ttf")):
        with pytest.raises(ValueError):
            fonts.resolve(bad)


def test_config_validates_fonts():
    with pytest.raises(ValueError, match="font_primary"):
        Config(font_primary="nope")
    assert Config(font_secondary=" INTER ").font_secondary == "inter"


def test_custom_primary_font(tmp_path):
    reg = _copy(tmp_path)
    base = PdfReader(str(export_agenda(Config(**SMALL), tmp_path / "a.pdf")))
    cust = PdfReader(str(export_agenda(Config(**SMALL, font_primary=str(reg)), tmp_path / "b.pdf")))
    # BaseFont comes from the font's internal name, so use a different Inter style as "bold"
    shutil.copy(INTER / "Inter-Italic.ttf", tmp_path / "MyFont-Bold.ttf")
    cust = PdfReader(str(export_agenda(Config(**SMALL, font_primary=str(reg)), tmp_path / "c.pdf")))
    names = _base_fonts(cust)
    assert not any("Italic" in n for n in _base_fonts(base))
    assert any("InterItalic" in n for n in names) and any(n.endswith("+Inter") for n in names)
    assert [p.extract_text() for p in cust.pages] == [p.extract_text() for p in base.pages]


def test_cli_font_flags(tmp_path, capsys):
    reg = _copy(tmp_path)
    out = tmp_path / "c.pdf"
    args = ["--year", "2026", "--planners", "weekly", "--daily-months", "", "-o", str(out)]
    assert main([*args, "--font-primary", str(reg), "--font-secondary", "inter"]) in (0, None)
    assert main([*args, "--font-primary", "nope"]) == 2


def test_no_inter_literal_in_draw_code():
    files = [ROOT / "agenda" / "draw.py", *(ROOT / "agenda" / "pages").glob("*.py")]
    for f in files:
        assert 'set_font("Inter"' not in f.read_text(), f
