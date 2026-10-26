"""Filler slots before week spreads: weekly_filler / daily_filler (blank, none or a page)."""

import pytest
from pydantic import ValidationError

from agenda.assembler import build_plan
from agenda.cli import main
from agenda.config import Config
from agenda.configfile import flatten
from agenda.exporter import render_pages
from agenda.gui.bar_model import tooltip_text
from agenda.pages.core import Daily, Notes, Weekly


def _fillers(plan):
    return [e for e in plan if e.kind == "filler"]


def test_defaults_are_blank():
    cfg = Config(year=2026)
    assert (cfg.weekly_filler, cfg.daily_filler) == ("blank", "blank")
    fillers = _fillers(build_plan(cfg))
    assert len(fillers) == 41 and all(e.is_blank and e.section == "weekly" for e in fillers)


@pytest.mark.parametrize("field", ["weekly_filler", "daily_filler"])
def test_validation(field):
    assert getattr(Config(**{field: " Notes "}), field) == "notes"
    assert getattr(Config(**{field: "NONE"}), field) == "none"
    for bad in ("nope", "weekly"):  # unknown id; a 2-page spread
        with pytest.raises(ValidationError, match=field):
            Config(**{field: bad})


def test_daily_filler_page_follows_day_pages():
    plan = build_plan(Config(year=2026, daily_filler="notes"))
    fillers = _fillers(plan)
    after_daily = [e for e in fillers if plan[e.page_number - 2].page_class is Daily]
    assert after_daily and all(e.page_class is Notes for e in after_daily)
    assert all(e.is_blank for e in fillers if e not in after_daily)
    for e in fillers:  # the filler still puts the spread on a left page
        assert plan[e.page_number].page_class is Weekly and plan[e.page_number].side == "left"


def test_weekly_filler_without_day_pages():
    plan = build_plan(Config(year=2026, planners=["weekly"], weekly_filler="todo"))
    fillers = _fillers(plan)
    assert fillers and all(e.page_class.id == "todo" for e in fillers)


def test_none_drops_fillers_and_spreads_may_start_right():
    cfg = Config(year=2026, weekly_filler="none", daily_filler="none")
    plan = build_plan(cfg)
    assert not _fillers(plan)
    assert len(plan) % 4 == 0  # padding still completes the booklets
    starts = [e for e in plan if e.page_class is Weekly and e.page_in_instance == 0]
    assert {e.side for e in starts} == {"left", "right"}
    i = next(e.page_number - 1 for e in starts if e.side == "right")
    assert render_pages(cfg, plan, [i, i + 1]).startswith(b"%PDF")


def test_filler_page_renders_and_has_a_tooltip():
    cfg = Config(year=2026, daily_filler="notes")
    plan = build_plan(cfg)
    e = next(e for e in _fillers(plan) if not e.is_blank)
    assert render_pages(cfg, plan, [e.page_number - 1]).startswith(b"%PDF")
    assert "Notes (filler)" in tooltip_text(plan, e.page_number - 1)


def test_yaml_blocks_and_cli(tmp_path):
    flat = flatten({"weekly": {"filler": "notes"}, "daily": {"filler": "none"}})
    assert flat == {"weekly_filler": "notes", "daily_filler": "none"}
    out = tmp_path / "a.pdf"
    args = ["--year", "2026", "--planners", "weekly", "--weekly-filler", "none", "--dry-run"]
    assert main([*args, "--output", str(out)]) in (None, 0)
