import pytest
from pydantic import ValidationError

from agenda.assembler import build_plan
from agenda.config import Config


def _ids(plan):
    return [(e.page_class.id if e.page_class else None, e.ctx.get("month")) for e in plan.entries]


def test_start_and_end_pages_inside_each_month():
    cfg = Config(
        month_start_pages=["budget", "habits"],
        month_end_pages=["monthly_review"],
        pages=["budget", "todo"],
    )
    plan = build_plan(cfg)
    ids = _ids(plan)
    for m in range(1, 13):
        i = ids.index(("monthly", m))
        assert ids[i + 1 : i + 3] == [("budget", m), ("habits", m)]
        j = ids.index(("monthly_review", m))
        nxt = ids[j + 1 :]
        if m < 12:
            assert nxt[0] == ("monthly", m + 1)
        assert all(
            e.section == "monthly"
            for e in plan.entries
            if e.page_class and e.page_class.id in ("budget", "habits", "monthly_review")
        )
    names = [i for i, _ in ids]
    assert names.count("budget") == 12  # not repeated in the optional block
    assert names.count("todo") == 1


def test_validation():
    with pytest.raises(ValidationError, match="not both"):
        Config(month_start_pages=["budget"], month_end_pages=["budget"])
    with pytest.raises(ValidationError, match="per-month"):
        Config(month_start_pages=["todo"])
    with pytest.raises(ValidationError, match="unknown"):
        Config(month_end_pages=["nope"])
    with pytest.raises(ValidationError, match="twice"):
        Config(month_end_pages=["quotes", "quotes"])


def test_booklets_stay_whole():
    cfg = Config(month_start_pages=["habits"], month_end_pages=["quotes", "health"])
    plan = build_plan(cfg)
    assert len(plan.entries) % 4 == 0


def test_cli_flags():
    from agenda.cli import build_overrides

    out = build_overrides(month_start_pages="budget, habits", month_end_pages="quotes")
    assert out == {"month_start_pages": ["budget", "habits"], "month_end_pages": ["quotes"]}
