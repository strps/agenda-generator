import pytest

from agenda import templates as T
from agenda.catalog import get_page, preset_pages
from agenda.config import Config
from agenda.configfile import ConfigFileError, flatten, load_yaml
from agenda.gui.settings_model import default_values, load_values, save_yaml


def test_partition_and_page_ids():
    seen = []
    for s in T.SECTIONS:
        for f in s.fields.values():
            assert f in Config.model_fields
        seen += list(s.fields.values())
        if s.page_id:
            get_page(s.page_id)
        assert s.enable in T.ENABLE_KINDS
    assert len(seen) == len(set(seen))
    union = [f for s in T.SECTIONS for f in T.fields_of(s.key, Config.model_fields)]
    assert sorted(union) == sorted(Config.model_fields)
    assert T.TEMPLATE_KEYS == (
            "notes",
            "daily",
            "weekly",
            "schedule",
            "habits",
            "qr",
            "niche_entrepreneur",
            "niche_student",
            "niche_fitness",
        )


def test_group_of_and_order():
    assert T.group_of("daily_months") == "daily"
    assert T.group_of("pad_with") == T.group_of("notes_pattern") == "notes"
    assert T.group_of("theme") == T.STYLING
    assert T.group_of("planners") == T.group_of("pages") == T.group_of("year") == T.GLOBAL
    assert T.SECTIONS[0].key == T.GLOBAL
    assert T.SECTIONS[1].key == "notes"
    assert T.SECTIONS[-1].key == T.STYLING
    with pytest.raises(KeyError):
        T.section("nope")


def test_is_enabled():
    assert not T.is_enabled(Config(planners=["weekly"]), "daily")
    assert T.is_enabled(Config(planners=["weekly"]), "weekly")
    assert not T.has_enable_box("notes")
    assert T.has_enable_box("qr")
    assert T.is_enabled(Config(pages=["qr"], qr_urls=["x"]), "qr")
    assert T.is_enabled(Config(), "notes")


def test_with_enabled():
    v = default_values()
    assert T.with_enabled(v, "daily", False)["planners"] == ["weekly"]
    assert T.with_enabled({**v, "planners": ["weekly"]}, "daily", True)["planners"] == [
        "weekly",
        "daily",
    ]
    out = T.with_enabled({**v, "preset": "essential"}, "qr", True)

    assert out["pages"] == list(dict.fromkeys(preset_pages("essential") + ["qr"]))
    again = T.with_enabled(out, "qr", True)
    assert again["pages"].count("qr") == 1
    assert "qr" not in T.with_enabled(out, "qr", False)["pages"]
    with pytest.raises(ValueError):
        T.with_enabled(v, "notes", False)


def test_flatten_blocks():
    flat = flatten(
        {
            "daily": {"months": "1-3"},
            "notes": {"pattern": "grid", "pad_with": "notes"},
            "style": {"theme": "x"},
        }
    )
    assert flat == {
        "daily_months": "1-3",
        "notes_pattern": "grid",
        "pad_with": "notes",
        "theme": "x",
    }


def test_flatten_errors():
    with pytest.raises(ConfigFileError):
        flatten({"daily": 3})
    with pytest.raises(ConfigFileError, match="months"):
        flatten({"daily": {"bogus": 1}})
    with pytest.raises(ConfigFileError):
        flatten({"daily": {"months": [1]}, "daily_months": [2]})


def test_block_and_flat_yaml_equal(tmp_path):
    a = tmp_path / "a.yaml"
    b = tmp_path / "b.yaml"
    a.write_text("year: 2027\ndaily_months: [1, 2]\nnotes_pattern: grid\ntheme: t\n")
    b.write_text("year: 2027\ndaily: {months: [1, 2]}\nnotes: {pattern: grid}\nstyle: {theme: t}\n")
    assert Config(**load_yaml(a)) == Config(**load_yaml(b))


def test_repo_sample_loads():
    Config(**load_yaml("config.yaml"))


def test_save_grouped_roundtrip(tmp_path):
    import yaml

    cfg = Config(
        daily_months=[1, 2],
        notes_pattern="grid",
        qr_urls=["https://a"],
        theme="x",
        pages=["qr"],
    )
    path = tmp_path / "c.yaml"
    save_yaml(cfg, path)
    data = yaml.safe_load(path.read_text())
    assert isinstance(data["daily"], dict) and isinstance(data["style"], dict)
    assert "daily_months" not in data
    assert Config(**load_values(path)) == cfg
