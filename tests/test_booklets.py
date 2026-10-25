import pytest

from agenda.assembler import (
    booklet_index_for,
    build_plan,
    pages_per_booklet,
    pages_per_sheet,
    plan_booklets,
)
from agenda.config import Config


@pytest.mark.parametrize(
    ("size", "unit", "folded", "expected"),
    [
        (5, "sheets", True, 20),
        (5, "sheets", False, 10),
        (1, "sheets", True, 4),
        (1, "sheets", False, 2),
        (24, "pages", True, 24),
        (10, "pages", False, 10),
    ],
)
def test_pages_per_booklet(size, unit, folded, expected):
    assert pages_per_booklet(size, unit, folded) == expected


def test_pages_per_sheet():
    assert (pages_per_sheet(True), pages_per_sheet(False)) == (4, 2)


def test_matches_config_property():
    for unit in ("sheets", "pages"):
        for folded in (True, False):
            c = Config(booklet_size=8, booklet_unit=unit, booklet_folded=folded)
            assert pages_per_booklet(8, unit, folded) == c.pages_per_booklet


def test_exact_fit():
    b = plan_booklets(40, 20)
    assert (b.count, b.padding, b.overflow) == (2, 0, 0)


def test_partial_last_booklet():
    b = plan_booklets(45, 20)
    assert (b.count, b.padding) == (3, 15)


def test_one_page():
    b = plan_booklets(1, 20)
    assert (b.count, b.padding) == (1, 19)


def test_one_sheet_booklets():
    assert plan_booklets(9, 4).count == 3 and plan_booklets(9, 4).padding == 3
    assert plan_booklets(9, 2).padding == 1


def test_zero_pages_auto_is_one_booklet():
    assert plan_booklets(0, 4).count == 1


def test_fixed_num_booklets_pads_up():
    b = plan_booklets(30, 20, 3)
    assert (b.count, b.padding, b.overflow) == (3, 30, 0)


def test_fixed_num_booklets_overflow():
    b = plan_booklets(50, 20, 2)
    assert (b.count, b.padding, b.overflow) == (2, 0, 10)


def test_bad_size():
    with pytest.raises(ValueError):
        plan_booklets(5, 0)


def test_booklet_index_for():
    assert [booklet_index_for(p, 4) for p in (1, 4, 5, 8, 9)] == [1, 1, 2, 2, 3]


@pytest.mark.parametrize(
    ("kw", "per"),
    [
        ({}, 20),
        ({"booklet_folded": False}, 10),
        ({"booklet_size": 1}, 4),
        ({"booklet_size": 8, "booklet_unit": "pages"}, 8),
    ],
)
def test_build_plan_sets_booklet_index(kw, per):
    plan = build_plan(Config(**kw))
    assert all(e.booklet_index == (e.page_number - 1) // per + 1 for e in plan)
    assert plan[0].booklet_index == 1
    assert len(plan.by_booklet(1)) == per
