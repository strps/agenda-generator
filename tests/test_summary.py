from agenda.assembler import LARGE_PAGE_COUNT, build_plan, make_entry, summarize
from agenda.config import Config
from agenda.pages.core import Notes


def _cfg(**kw):
    return Config(year=kw.pop("year", 2026), **kw)


def _sum(**kw):
    cfg = _cfg(**kw)
    return build_plan(cfg), summarize(build_plan(cfg), cfg)


def test_default_numbers():
    # Default: 5 folded sheets = 20 pages per booklet, 4 pages per sheet.
    plan, s = _sum()
    assert s.total_pages == len(plan) == s.counted_pages
    assert s.cover_pages == 0
    assert s.pages_per_booklet == 20 and s.sheets_per_booklet == 5
    assert s.booklets * 20 == s.total_pages  # padding makes the total a whole number of booklets
    assert s.total_sheets == s.booklets * 5 == s.total_pages // 4
    assert s.padding_pages == sum(e.kind == "padding" for e in plan)
    assert s.fillers == sum(e.kind == "filler" for e in plan)
    assert s.blank_padding == 0 and s.overflow == 0
    assert s.total_pages <= LARGE_PAGE_COUNT and s.warnings == ()


def test_separate_covers():
    _, s = _sum(separate_covers=True)
    # Cover, inside-cover, inside-back, back cover are outside the booklets.
    assert s.cover_pages == 4 and s.counted_pages == s.total_pages - 4
    assert s.counted_pages % 20 == 0 and s.booklets == s.counted_pages // 20
    assert s.fillers >= 2


def test_flat():
    # Flat: 2 pages per sheet, 5 sheets -> 10 pages per booklet.
    _, s = _sum(booklet_folded=False)
    assert s.pages_per_booklet == 10 and s.sheets_per_booklet == 5
    assert s.total_sheets == s.total_pages // 2


def test_overflow_warning():
    _, s = _sum(num_booklets=2)
    assert s.overflow == s.total_pages - 40 > 0 and s.booklets == 2
    assert any("num_booklets" in w for w in s.warnings)
    assert "Warning" in str(s)


def test_large_agenda_warning():
    cfg = _cfg()
    from agenda.assembler import PagePlan

    plan = PagePlan(
        tuple(make_entry(Notes, {}, i, "notes") for i in range(1, LARGE_PAGE_COUNT + 21))
    )
    s = summarize(plan, cfg)
    assert any("daily_months" in w for w in s.warnings)


def test_small_agenda_no_warnings():
    _, s = _sum(planners=["weekly"])
    assert s.warnings == ()
    assert "Booklets:" in s.format()


def test_blank_padding_warning():
    cfg = _cfg()
    from agenda.assembler import PagePlan

    entries = [make_entry(Notes, {}, i, "notes") for i in range(1, 20)]
    entries.append(make_entry(None, {}, 20, "front_back", kind="padding"))
    s = summarize(PagePlan(tuple(entries)), cfg)
    assert s.blank_padding == 1 and any("blank padding" in w for w in s.warnings)
