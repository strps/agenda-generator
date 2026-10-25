from datetime import date

from agenda.assembler import build_plan
from agenda.config import Config
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
    assert all(e.booklet_index is None for e in plan)
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
