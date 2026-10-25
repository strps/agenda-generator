import dataclasses

import pytest

from agenda.assembler import PagePlan, PlanEntry, make_entry
from agenda.pages.core import Monthly, Weekly


def _plan():
    wk = {"number": 1}
    return PagePlan.from_entries(
        [
            make_entry(Monthly, {"month": 1}, 1, "monthly"),
            make_entry(None, {}, 2, "weekly", kind="filler"),
            make_entry(Weekly, wk, 3, "weekly"),
            make_entry(Weekly, wk, 4, "weekly", page_in_instance=1, booklet_index=1),
        ]
    )


def test_side_from_grid():
    assert [e.side for e in _plan()] == ["right", "left", "right", "left"]


def test_len_iter_index():
    p = _plan()
    assert len(p) == p.page_count == 4
    assert p[0].page_class is Monthly
    assert [e.page_number for e in p] == [1, 2, 3, 4]


def test_frozen_defaults():
    e = make_entry(Monthly, {}, 1, "monthly")
    assert e.booklet_index is None and e.kind == "page" and e.page_in_instance == 0
    with pytest.raises(dataclasses.FrozenInstanceError):
        e.section = "x"  # type: ignore[misc]


def test_blank_and_drawn():
    p = _plan()
    assert p[1].is_blank
    drawn = p.drawn()
    assert [e.page_number for e in drawn] == [1, 3]
    assert p[2].ctx is p[3].ctx


def test_queries():
    p = _plan()
    assert [e.page_number for e in p.by_section("weekly")] == [2, 3, 4]
    assert [e.page_number for e in p.by_booklet(1)] == [4]
    assert p.sections() == [("monthly", 1, 1), ("weekly", 2, 4)]
    assert PagePlan().sections() == [] and len(PagePlan()) == 0


def test_validation():
    with pytest.raises(ValueError):
        PagePlan.from_entries([make_entry(Monthly, {}, 2, "monthly")])
    bad = PlanEntry(Monthly, {}, 1, "left", None, "monthly")
    with pytest.raises(ValueError):
        PagePlan.from_entries([bad])
    with pytest.raises(ValueError):
        make_entry(Monthly, {}, 0, "monthly")
