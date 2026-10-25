from agenda.assembler import build_plan
from agenda.config import Config
from agenda.pages.core import Daily, Weekly


def _plan(**kw):
    return build_plan(Config(year=kw.pop("year", 2026), **kw))


def _dates(plan):
    return [e.ctx["date"] for e in plan if e.page_class is Daily]


def test_default_all_days():
    assert len(_dates(_plan())) == 365


def test_january_only_keeps_weeks():
    full, jan = _plan(), _plan(daily_months=[1])
    d = _dates(jan)
    assert len(d) == 31 and {x.month for x in d} == {1}
    weeks = lambda p: sum(e.page_class is Weekly for e in p)
    assert weeks(jan) == weeks(full)
    assert jan.page_count < full.page_count


def test_spec_string():
    d = _dates(_plan(daily_months="1-3,6"))
    assert len(d) == 31 + 28 + 31 + 30
    assert {x.month for x in d} == {1, 2, 3, 6}


def test_week_spanning_two_months():
    # 2026-03-30 (Mon) .. 04-05 spans March/April.
    d = _dates(_plan(daily_months=[4]))
    assert len(d) == 30 and {x.month for x in d} == {4}
    assert d == sorted(d)


def test_daily_only_planner():
    plan = _plan(planners=["daily"], daily_months=[2])
    assert len(_dates(plan)) == 28
    assert not any(e.page_class is Weekly for e in plan)


def test_page_count_multiple_of_booklet():
    full, jan = _plan(), _plan(daily_months=[1])
    assert jan.page_count < full.page_count
    for p in (full, jan):
        sizes = {len(list(p.by_booklet(i))) for i in {e.booklet_index for e in p}}
        assert len(sizes) == 1
        assert [e.page_number for e in p] == list(range(1, len(p) + 1))
