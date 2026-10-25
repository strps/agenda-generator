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
    # 2-page spread starting left, odd booklet size: cannot always fill exactly
    cfg = _cfg(planners=["weekly"], pad_with="weekly", booklet_unit="pages", booklet_size=7,
               booklet_folded=False)  # fmt: skip
    plan = build_plan(cfg)
    assert len(plan) % 7 == 0
    assert plan[-1].page_class is BackCover
    assert all(e.page_class in (Weekly, None) for e in _padding(plan))


def test_fixed_num_booklets_fills_and_overflow_adds_none():
    cfg = _cfg(planners=["weekly"], num_booklets=30)
    assert len(build_plan(cfg)) == 30 * _per(cfg)
    small = _cfg(planners=["weekly"], num_booklets=1)
    assert not _padding(build_plan(small))
