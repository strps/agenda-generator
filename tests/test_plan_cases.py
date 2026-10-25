"""Plan-level cases: invariants checked by one helper over default and edge configs."""

from datetime import date, timedelta

import pytest
from pypdf import PdfReader

from agenda.assembler import (
    build_plan,
    pages_per_booklet,
    plan_booklets,
    summarize,
)
from agenda.calendar import days_of_year
from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.grid import side_for_page
from agenda.pages.core import BackCover, Cover, Daily, Weekly

# "1 page" cannot be literal (cover, info, yearly, 12 monthlies, notes, contacts, back cover
# are always present). The smallest plan: no planners, no extra pages.
MINIMAL = {"planners": [], "pages": []}

CASES = {
    "default": {},
    "minimal": MINIMAL,
    "minimal_one_booklet": dict(MINIMAL, num_booklets=1, booklet_size=5),
    "sheet_folded": {"booklet_size": 1},
    "sheet_flat": {"booklet_size": 1, "booklet_folded": False},
    "minimal_sheet_folded": dict(MINIMAL, booklet_size=1),
    "minimal_sheet_flat": dict(MINIMAL, booklet_size=1, booklet_folded=False),
    "weekly_only": {"planners": ["weekly"]},
    "daily_only": {"planners": ["daily"]},
    "separate_covers": {"separate_covers": True},
    "daily_months": {"daily_months": [1, 12]},
    "flat_pages": {"booklet_size": 6, "booklet_unit": "pages", "booklet_folded": False},
    "sunday": {"week_start": "sunday"},
}


def check_plan(cfg):
    plan = build_plan(cfg)
    n = len(plan)
    assert n >= 1
    for i, e in enumerate(plan):
        assert e.page_number == i + 1
        assert e.side == side_for_page(i + 1)
    # spreads: paired, shared ctx, start on the declared side
    for i, e in enumerate(plan):
        if e.page_class is None or e.kind == "filler":
            continue
        cls = e.page_class
        if e.page_in_instance == 0:
            if cls.starts_on != "any":
                assert e.side == cls.starts_on
            for k in range(cls.pages):
                assert plan[i + k].page_class is cls and plan[i + k].page_in_instance == k
                assert plan[i + k].ctx is e.ctx
    # cover first, back cover last
    assert plan[0].page_class is Cover
    assert plan[-1].page_class is BackCover and plan[-1].page_in_instance == 0
    # padding is contiguous and right before the back cover (a cover filler may sit between)
    pads = [i for i, e in enumerate(plan) if e.kind == "padding"]
    if pads:
        assert pads == list(range(pads[0], pads[-1] + 1))
        tail = [e for e in plan.entries[pads[-1] + 1 :]]
        assert all(e.kind == "filler" or e.page_class is BackCover for e in tail)
    # booklets: monotonic, every counted booklet full
    per = pages_per_booklet(cfg.booklet_size, cfg.booklet_unit, cfg.booklet_folded)
    counted = [e for e in plan if e.booklet_index is not None]
    idx = [e.booklet_index for e in counted]
    assert idx == sorted(idx) and idx[0] == 1
    s = summarize(plan, cfg)
    lay = plan_booklets(len(counted), per, cfg.num_booklets)
    if lay.overflow == 0:
        for b in range(1, idx[-1] + 1):
            assert len(plan.by_booklet(b)) == per
    if not cfg.separate_covers:
        assert len(counted) == n
    # summary consistent
    assert s.total_pages == n and s.counted_pages == len(counted)
    assert s.cover_pages == n - len(counted)
    assert s.booklets == lay.count == idx[-1]
    assert s.pages_per_booklet == per and s.overflow == lay.overflow == 0
    assert s.fillers == sum(e.kind == "filler" for e in plan)
    assert s.padding_pages == len(pads)
    if cfg.booklet_folded:
        assert len(counted) % 4 == 0
    return plan, s


@pytest.mark.parametrize("name", CASES)
def test_invariants(name):
    check_plan(Config(year=2026, **CASES[name]))


def test_minimal_contents():
    plan, s = check_plan(Config(year=2026, **MINIMAL))
    assert not any(e.page_class in (Daily, Weekly) for e in plan)
    assert len(plan) < 30
    assert s.booklets == 1 or s.booklets * s.pages_per_booklet == len(plan)


def test_one_sheet_booklets():
    folded = check_plan(Config(year=2026, **CASES["sheet_folded"]))[1]
    flat = check_plan(Config(year=2026, **CASES["sheet_flat"]))[1]
    assert (folded.pages_per_booklet, flat.pages_per_booklet) == (4, 2)
    assert folded.sheets_per_booklet == flat.sheets_per_booklet == 1
    assert folded.booklets == folded.total_pages // 4
    assert flat.booklets == flat.total_pages // 2


def test_weekly_and_daily_only_counts():
    w = build_plan(Config(year=2026, planners=["weekly"]))
    d = build_plan(Config(year=2026, planners=["daily"]))
    assert sum(e.page_class is Daily for e in w) == 0
    assert sum(e.page_class is Weekly for e in d) == 0
    assert sum(e.page_class is Daily for e in d) == 365


@pytest.mark.parametrize("year", range(2021, 2031))
@pytest.mark.parametrize("week_start", ["monday", "sunday"])
def test_every_day_has_one_daily_in_order(year, week_start):
    plan = build_plan(Config(year=year, week_start=week_start))
    dates = [e.ctx["date"] for e in plan if e.page_class is Daily]
    assert dates == days_of_year(year)


def test_orphan_placement_2027_and_2024():
    plan = build_plan(Config(year=2027))  # Jan 1-3 are in ISO week 53 of 2026
    i = next(i for i, e in enumerate(plan) if e.page_class is Daily)
    assert plan[i].ctx["date"] == date(2027, 1, 1)
    assert plan[i - 1].section == "monthly" and plan[i + 3].page_class is Weekly
    assert plan[i + 2].ctx["date"] == date(2027, 1, 3)
    plan = build_plan(Config(year=2024))  # Dec 30-31 are in ISO week 1 of 2025
    ds = [e.ctx["date"] for e in plan if e.page_class is Daily]
    assert ds[-2:] == [date(2024, 12, 30), date(2024, 12, 31)]
    assert ds[-1] - ds[0] == timedelta(days=365)


def test_orphans_respect_daily_months():
    plan = build_plan(Config(year=2027, daily_months=[1]))
    ds = [e.ctx["date"] for e in plan if e.page_class is Daily]
    assert len(ds) == 31 and ds[0] == date(2027, 1, 1)


def test_export_agenda_pdf_matches_plan(tmp_path):
    cfg = Config(year=2026, daily_months=[1])
    out = export_agenda(cfg, tmp_path / "a.pdf")
    assert len(PdfReader(out).pages) == len(build_plan(cfg))
