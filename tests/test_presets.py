"""Presets by value score: catalog selection, Config resolution, plan validity."""

import pytest

from agenda import catalog
from agenda.assembler import build_plan
from agenda.catalog import all_pages, get_page, preset_pages
from agenda.config import Config
from agenda.pages.base import BasePage

NAMES = ("essential", "complete", "premium")
SIZES = ("a5", "b6", "letter")


def test_nesting_and_membership():
    ess, com, pre = (set(preset_pages(n)) for n in NAMES)
    assert ess <= com <= pre
    assert ess < pre
    non_core = {p.id for p in all_pages() if p.category != "core"}
    assert pre == non_core
    for n in NAMES:
        ids = preset_pages(n)
        assert len(ids) == len(set(ids))
        assert all(get_page(i).category != "core" for i in ids)


def test_thresholds():
    assert "qr" in preset_pages("essential")
    assert "vision_board" not in preset_pages("essential")
    assert "vision_board" in preset_pages("complete")
    assert "quotes" not in preset_pages("complete")
    assert "goals" not in preset_pages("complete")  # unscored: premium only
    assert "goals" in preset_pages("premium")


def test_unknown_name():
    with pytest.raises(ValueError, match="essential, complete, premium"):
        preset_pages("deluxe")


def test_scores_drive_membership(monkeypatch):
    monkeypatch.setattr(get_page("quotes"), "added_value", 5)
    assert "quotes" in preset_pages("essential")
    saved = dict(catalog.CATALOG)
    try:
        cls = type(
            "Fake",
            (BasePage,),
            {
                "id": "fake_hi",
                "name": "f",
                "category": "value_added",
                "section": "value_added",
                "added_value": 4,
                "draw": lambda self, pdf, ctx, config, grids: None,
            },
        )
        catalog.register(cls)
        assert "fake_hi" in preset_pages("complete")
        assert "fake_hi" not in preset_pages("essential")
    finally:
        catalog.CATALOG.clear()
        catalog.CATALOG.update(saved)


def test_config_fills_pages_from_preset():
    assert Config().pages is None
    for n in NAMES:
        assert Config(preset=n).pages == preset_pages(n)


def test_explicit_pages_win():
    assert Config(preset="premium", pages=["goals"]).pages == ["goals"]


def test_invalid_preset():
    with pytest.raises(ValueError):
        Config(preset="nope")


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("name", NAMES)
def test_preset_builds_valid_plan(name, size):
    cfg = Config(preset=name, page_size=size, qr_urls=["https://example.org"])
    plan = build_plan(cfg)
    assert plan.page_count == len(plan)
    per = cfg.pages_per_booklet
    assert plan.page_count % per == 0
    ids = {e.page_class.id for e in plan if e.page_class}
    assert set(preset_pages(name)) <= ids | {"qr"}
    assert "qr" in ids


@pytest.mark.parametrize("name", NAMES)
def test_preset_without_urls_still_valid(name):
    plan = build_plan(Config(preset=name))
    assert not any(e.page_class and e.page_class.id == "qr" for e in plan)
    assert plan.page_count % Config().pages_per_booklet == 0
