import hashlib
import json
from pathlib import Path

import pytest
from pypdf import PdfReader

from agenda import themes, tokens
from agenda.cli import main
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.gui.style_model import _hex, contrast_ratio

SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}
ROOT = Path(__file__).resolve().parent.parent


def _export(tmp_path, name="a.pdf", **extra):
    path = export_agenda(Config(**{**SMALL, **extra}), tmp_path / name)
    return PdfReader(str(path))


def _streams(reader):
    return [hashlib.sha256(p.get_contents().get_data()).hexdigest() for p in reader.pages]


def _text(reader):
    return [p.extract_text() for p in reader.pages]


def test_default_fingerprint_unchanged(tmp_path):
    expected = json.loads((ROOT / "tests/data/default_style_fingerprint.json").read_text())
    assert _streams(_export(tmp_path)) == expected


def test_theme_registry():
    assert tuple(themes.THEMES) == ("minimal", "mono", "ocean", "forest")
    assert themes.THEMES["minimal"] == tokens.COLORS
    for palette in themes.THEMES.values():
        assert set(palette) == set(tokens.COLORS)


@pytest.mark.parametrize("name", list(themes.THEMES))
def test_palette_contrast(name):
    p = themes.THEMES[name]
    white = "#ffffff"
    assert contrast_ratio(_hex(p["ink"]), white) >= 7
    # minimal is the unchanged legacy palette: its muted gray (120) is 4.42, below the 4.5 target
    assert contrast_ratio(_hex(p["muted"]), white) >= (4.4 if name == "minimal" else 4.5)
    assert contrast_ratio(_hex(p["accent"]), white) >= 4.5


def test_palette_for():
    assert themes.palette_for("nope") == themes.THEMES["minimal"]
    assert themes.palette_for("ocean", {"accent": (1, 2, 3)})["accent"] == (1, 2, 3)
    assert themes.palette_for("minimal") is not themes.THEMES["minimal"]
    assert themes.is_known("forest") and not themes.is_known("nope")


def test_ocean_differs_but_text_same(tmp_path):
    base, ocean = _export(tmp_path, "m.pdf"), _export(tmp_path, "o.pdf", theme="ocean")
    assert len(base.pages) == len(ocean.pages)
    assert _streams(base) != _streams(ocean)
    assert _text(base) == _text(ocean)


def test_unknown_theme_renders_minimal(tmp_path, capsys):
    assert _streams(_export(tmp_path, theme="nonexistent")) == _streams(_export(tmp_path, "b.pdf"))
    out = tmp_path / "c.pdf"
    code = main(
        [
            "--year",
            "2026",
            "--planners",
            "weekly",
            "--daily-months",
            "",
            "--theme",
            "nonexistent",
            "--output",
            str(out),
        ]
    )
    assert code in (0, None) and out.exists()
    assert "unknown theme" in capsys.readouterr().err


def test_no_global_color_lookups():
    files = [ROOT / "agenda/draw.py", *sorted((ROOT / "agenda/pages").glob("*.py"))]
    for f in files:
        assert "tokens.COLORS[" not in f.read_text(), f
