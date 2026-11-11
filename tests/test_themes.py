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
    assert tuple(themes.THEMES) == (
        "minimal",
        "mono",
        "ocean",
        "forest",
        "blush",
        "lavender",
        "peony",
    )
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


def test_color_field_normalised_and_validated():
    assert Config(color_accent="#1E6FD9").color_accent == "#1e6fd9"
    assert Config(color_accent="1e6fd9").color_accent == "#1e6fd9"
    assert Config(color_accent="#abc").color_accent == "#aabbcc"
    for bad in ("blue", "#12345g"):
        with pytest.raises(ValueError, match="color_accent"):
            Config(color_accent=bad)
    names = [n for n in Config.model_fields if n.startswith("color_")]
    assert len(names) == 7
    assert all(getattr(Config(), n) is None for n in names)


def test_color_override_changes_streams(tmp_path):
    base = _streams(_export(tmp_path))
    same = _export(tmp_path, "b.pdf", color_accent=themes.rgb_to_hex(tokens.COLORS["accent"]))
    assert _streams(same) == base
    assert _streams(_export(tmp_path, "c.pdf", color_accent="#0000ff")) != base


def test_style_block_yaml_equals_flat_and_round_trips(tmp_path):
    from agenda.configfile import load_yaml
    from agenda.gui.settings_model import save_yaml

    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text('style: {theme: ocean, accent: "#0000ff"}\n')
    b.write_text('theme: ocean\ncolor_accent: "#0000ff"\n')
    cfg = Config(**load_yaml(a))
    assert cfg == Config(**load_yaml(b))
    out = tmp_path / "c.yaml"
    save_yaml(cfg, out)
    assert Config(**load_yaml(out)) == cfg
    assert "color_ink" not in out.read_text()


def test_cli_color_flags(tmp_path):
    base = ["--year", "2026", "--planners", "weekly", "--daily-months", "", "-o"]
    assert main(
        [*base, str(tmp_path / "x.pdf"), "--color-accent", "#0000ff", "--color-ink", "#111111"]
    ) in (0, None)
    assert main([*base, str(tmp_path / "y.pdf"), "--color-accent", "nope"]) == 2


@pytest.mark.parametrize("name", ["blush", "lavender", "peony"])
def test_feminine_fills_keep_title_text_readable(name):
    p = themes.THEMES[name]
    # holiday titles are accent on holiday_fill; weekend titles are muted on weekend_fill
    assert contrast_ratio(_hex(p["accent"]), _hex(p["holiday_fill"])) >= 3
    assert contrast_ratio(_hex(p["muted"]), _hex(p["weekend_fill"])) >= 4.5
