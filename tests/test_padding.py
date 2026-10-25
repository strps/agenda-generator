from agenda.assembler import build_plan, pages_per_booklet
from agenda.config import Config
from agenda.pages.core import BackCover, Contacts, Notes, Weekly


def _cfg(**kw):
    return Config(year=kw.pop("year", 2026), **kw)


def _per(cfg):
    return pages_per_booklet(cfg.booklet_size, cfg.booklet_unit, cfg.booklet_folded)


def _padding(plan):
    return [e for e in plan if e.kind == "padding"]


def test_default_total_multiple_of_booklet():
    cfg = _cfg()
    plan = build_plan(cfg)
    assert len(plan) % _per(cfg) == 0
    assert plan[-1].page_class is BackCover


def test_padding_sits_right_before_back_cover():
    plan = build_plan(_cfg(planners=["weekly"]))
    pad = _padding(plan)
    assert pad and all(e.page_class is Notes for e in pad)
    first, last = pad[0].page_number, pad[-1].page_number
    assert last == len(plan) - 1
    assert last - first + 1 == len(pad)  # contiguous
    assert plan[first - 2].page_class is Contacts


def test_booklet_index_still_right():
    cfg = _cfg(planners=["weekly"])
    plan = build_plan(cfg)
    per = _per(cfg)
    assert all(e.booklet_index == (e.page_number - 1) // per + 1 for e in plan)
    assert plan[-1].booklet_index == len(plan) // per


def test_zero_padding_on_exact_fit():
    base = build_plan(_cfg(planners=["weekly"]))
    # one booklet of exactly the unpadded size
    n = len(base) - len(_padding(base))
    cfg = _cfg(planners=["weekly"], booklet_unit="pages", booklet_size=n, booklet_folded=False)
    plan = build_plan(cfg)
    assert len(plan) == n and not _padding(plan)


def test_flat_vs_folded():
    for folded in (True, False):
        cfg = _cfg(planners=["weekly"], booklet_folded=folded, booklet_size=3)
        plan = build_plan(cfg)
        assert len(plan) % _per(cfg) == 0
    assert _per(_cfg(booklet_folded=False)) == 10


def test_pad_with_other_id_and_spread():
    cfg = _cfg(planners=["weekly"], pad_with="weekly")
    plan = build_plan(cfg)
    assert len(plan) % _per(cfg) == 0
    pad = _padding(plan)
    assert pad and all(e.page_class is Weekly for e in pad)
    assert plan[-1].page_class is BackCover


def test_spread_that_cannot_fill_falls_back_to_blank():
    # 2-page spread starting left, small booklet size: cannot always fill exactly
    cfg = _cfg(planners=["weekly"], pad_with="weekly", booklet_unit="pages", booklet_size=6,
               booklet_folded=False)  # fmt: skip
    plan = build_plan(cfg)
    assert len(plan) % 6 == 0
    assert plan[-1].page_class is BackCover
    assert all(e.page_class in (Weekly, None) for e in _padding(plan))


def test_fixed_num_booklets_fills_and_overflow_adds_none():
    cfg = _cfg(planners=["weekly"], num_booklets=30)
    assert len(build_plan(cfg)) == 30 * _per(cfg)
    small = _cfg(planners=["weekly"], num_booklets=1)
    assert not _padding(build_plan(small))


# separate_covers


def _inner(plan):
    return [e for e in plan if e.booklet_index is not None]


def test_separate_covers_default_unchanged():
    assert build_plan(_cfg()).entries[1].page_class is not None
    assert all(e.booklet_index for e in build_plan(_cfg()))


def _check_sep(cfg):
    plan = build_plan(cfg)
    per = _per(cfg)
    assert plan[0].page_class.__name__ == "Cover" and plan[0].booklet_index is None
    assert plan[1].is_blank and plan[1].booklet_index is None
    assert plan[-1].page_class is BackCover and plan[-1].booklet_index is None
    assert plan[-2].is_blank and plan[-2].booklet_index is None
    inner = _inner(plan)
    assert len(inner) % per == 0
    assert inner[0].page_number == 3 and inner[0].side == "right"
    assert inner[0].booklet_index == 1
    assert inner[-1].booklet_index == len(inner) // per
    return plan


def test_separate_covers_folded():
    cfg = _cfg(planners=["weekly"], separate_covers=True)
    plan = _check_sep(cfg)
    assert len(plan) == len(_inner(plan)) + 4


def test_separate_covers_flat():
    cfg = _cfg(planners=["weekly"], separate_covers=True, booklet_folded=False)
    _check_sep(cfg)


def test_separate_covers_padding_differs():
    a = build_plan(_cfg(planners=["weekly"]))
    b = build_plan(_cfg(planners=["weekly"], separate_covers=True))
    assert len(_inner(b)) % _per(_cfg()) == 0
    # inner block excludes the 2 covers: padding differs from the default by the cover pages
    assert len(_padding(a)) != len(_padding(b))


def test_separate_covers_fixed_num_booklets():
    cfg = _cfg(planners=["weekly"], separate_covers=True, num_booklets=8)
    plan = _check_sep(cfg)
    assert _inner(plan)[-1].booklet_index == 8


def test_folded_total_multiple_of_four_and_overflow_not_error():
    for kw in ({}, {"separate_covers": True}, {"booklet_unit": "pages", "booklet_size": 8}):
        plan = build_plan(_cfg(planners=["weekly"], **kw))
        counted = [e for e in plan if e.booklet_index is not None]
        assert len(counted) % 4 == 0
    # fixed num_booklets too small: plan overflows (a summary warning, not an error)
    plan = build_plan(_cfg(planners=["weekly"], num_booklets=1))
    assert plan.page_count > 20
