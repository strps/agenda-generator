from agenda.catalog import all_pages, catalog_rows, format_catalog, preset_pages
from agenda.pages.base import CATEGORIES


def test_rows_cover_registry_once():
    rows = catalog_rows()
    assert sorted(r["id"] for r in rows) == sorted(p.id for p in all_pages())


def test_rows_sorted_category_then_value_desc():
    rows = catalog_rows()
    keys = [(CATEGORIES.index(r["category"]), -r["value"], r["id"]) for r in rows]
    assert keys == sorted(keys)


def test_rows_presets_match_preset_pages():
    for r in catalog_rows():
        for name in ("essential", "complete", "premium"):
            assert (name in r["presets"]) == (r["id"] in preset_pages(name))
        if r["category"] == "core":
            assert r["presets"] == []


def test_format_catalog_pure():
    rows = [
        {"id": "a", "name": "Alpha", "category": "core", "value": 0, "presets": []},
        {
            "id": "longer_id",
            "name": "Beta",
            "category": "value_added",
            "value": 5,
            "presets": ["essential", "premium"],
        },
    ]
    lines = format_catalog(rows).splitlines()
    assert len(lines) == 3
    assert lines[0].split() == ["ID", "CATEGORY", "VALUE", "PRESETS", "NAME"]
    assert lines[1].split() == ["a", "core", "-", "-", "Alpha"]
    assert lines[2].split() == ["longer_id", "value_added", "5", "essential,premium", "Beta"]
    assert lines[1].index("core") == lines[2].index("value_added")
