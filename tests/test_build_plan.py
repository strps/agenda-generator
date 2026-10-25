from datetime import date

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.grid import side_for_page
from agenda.pages.core import (
    BackCover,
    Contacts,
    Cover,
    Daily,
    Monthly,
    Notes,
    PersonalInfo,
    Weekly,
    Yearly,
)  # fmt: skip


def _cfg(**kw):
    return Config(year=kw.pop("year", 2026), **kw)


def _runs(plan):
    return [s for s, _, _ in plan.sections()]


def test_default_order():
    plan = build_plan(_cfg())
    classes = [e.page_class for e in plan]
    assert classes[:3] == [Cover, PersonalInfo, Yearly]
    assert classes[3] is Monthly
    assert classes[-3:] == [Notes, Contacts, BackCover]
    assert [e.page_number for e in plan] == list(range(1, len(plan) + 1))
    assert all(e.booklet_index is not None for e in plan)
    assert sum(e.page_class is Monthly for e in plan) == 12
    assert sum(e.page_class is Weekly for e in plan) % 2 == 0
    assert _runs(plan)[0] == "front_back" and _runs(plan)[-1] == "front_back"
    # weekly spread is followed by 7 dailies (within the year)
    starts = [i for i, e in enumerate(plan) if e.page_class is Weekly and e.starts_instance]
    i = starts[1]  # the first week is partial
    assert plan[i].page_in_instance == 0 and plan[i + 1].page_in_instance == 1
    assert plan[i].ctx is plan[i + 1].ctx
    assert [e.page_class for e in plan[i + 2 : i + 9]] == [Daily] * 7


def test_weekly_only():
    plan = build_plan(_cfg(planners=["weekly"]))
    assert not any(e.page_class is Daily for e in plan)
    assert sum(e.page_class is Weekly for e in plan) > 0


def test_daily_only():
    plan = build_plan(_cfg(planners=["daily"]))
    assert not any(e.page_class is Weekly for e in plan)
    dates = [e.ctx["date"] for e in plan if e.page_class is Daily]
    assert len(dates) == 365 and dates == sorted(dates)


def test_week_crossing_month_and_year():
    plan = build_plan(_cfg(year=2026))  # Mon-start: week of 2026-03-30 crosses Mar/Apr
    weekly = [e for e in plan if e.page_class is Weekly and e.page_in_instance == 0]
    keys = [(e.ctx["iso_year"], e.ctx["number"]) for e in weekly]
    assert len(keys) == len(set(keys))  # each week placed once
    # 2026-12-28 starts ISO week 53 of 2026, which ends in 2027: dailies stop at Dec 31
    dailies = [e.ctx["date"] for e in plan if e.page_class is Daily]
    assert dailies[0] == date(2026, 1, 1) and dailies[-1] == date(2026, 12, 31)
    # 2026-01-01 week belongs to ISO 2026 W1 starting 2025-12-29: its spread precedes Jan 1
    first_week = weekly[0]
    j = plan.entries.index(first_week)
    assert plan[j + 2].page_class is Daily and plan[j + 2].ctx["date"] == date(2026, 1, 1)


def _reference_fillers(plan):
    """Replay export_agenda's rule over the real (non-filler) instances."""
    n = 0
    fillers = []
    for e in plan:
        if e.kind == "filler" or e.page_in_instance != 0:
            continue
        want = e.page_class.starts_on
        if want != "any" and side_for_page(n + 1) != want:
            fillers.append(n + 1)
            n += 1
        n += e.page_class.pages
    return fillers


def test_weekly_spreads_start_on_required_side():
    plan = build_plan(_cfg())
    starts = [e for e in plan if e.page_class is Weekly and e.page_in_instance == 0]
    assert len(starts) == 53
    assert all(e.side == "left" for e in starts)


def test_fillers_only_where_needed():
    plan = build_plan(_cfg())
    fillers = [e for e in plan if e.kind == "filler"]
    assert fillers and all(e.is_blank and not e.starts_instance for e in fillers)
    assert [e.page_number for e in fillers] == _reference_fillers(plan)
    for f in fillers:
        nxt = plan[f.page_number]  # entry after the filler
        assert nxt.page_class is not None and nxt.page_class.starts_on == nxt.side
        assert nxt.section == f.section
    # every other starts_on instance already lands on its side
    for e in plan:
        if e.starts_instance and e.page_class.starts_on != "any":
            assert e.side == e.page_class.starts_on


def test_no_fillers_without_constraint():
    plan = build_plan(_cfg(planners=["daily"]))
    assert not any(e.kind == "filler" for e in plan)
    assert plan.page_count == len(plan.drawn())


def test_month_boundary_week_placed_once_in_owning_month():
    plan = build_plan(_cfg(year=2026))  # Mon-start: week of 2026-03-30 is owned by March
    spreads = [e for e in plan if e.page_class is Weekly and e.starts_instance]
    hits = [e for e in spreads if e.ctx["days"][0] == date(2026, 3, 30)]
    assert len(hits) == 1
    i = plan.entries.index(hits[0])
    monthly = {e.ctx["month"]: e.page_number for e in plan if e.page_class is Monthly}
    assert monthly[3] < hits[0].page_number < monthly[4]
    # its dailies follow the spread: Mar 30, Mar 31, Apr 1 (week days all get dailies)
    assert [e.ctx["date"] for e in plan[i + 2 : i + 5] if e.page_class is Daily] == [
        date(2026, 3, 30), date(2026, 3, 31), date(2026, 4, 1),
    ]  # fmt: skip
