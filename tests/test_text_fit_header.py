"""Header text fit (header_text_fit) for the core pages and Daily holiday-name cuts."""

from __future__ import annotations

import pytest

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.exporter import export_agenda, render_pages
from agenda.textfit import CutLog

HOLIDAY = " ".join(
    ["An extraordinarily long holiday name that cannot possibly fit beside the week label"] * 3
)


def _narrow(mode, **kw):
    return Config(
        year=2027,
        page_size="50x100",
        font_primary_size=200,
        planners=["weekly"],
        header_text_fit=mode,
        **kw,
    )


def _log(cfg, tmp_path, name="a.pdf"):
    log = CutLog()
    export_agenda(cfg, tmp_path / name, cuts=log)
    return log


def _weekly_right_pages(cfg):
    plan = build_plan(cfg)
    return plan, [e.page_number for e in plan if e.ctx.get("days")]


def test_weekly_title_ellipsis_logged_with_page(tmp_path):
    cfg = _narrow("ellipsis")
    log = _log(cfg, tmp_path)
    assert log.pages("header")
    assert set(log.pages("header")) <= {e.page_number for e in build_plan(cfg)}
    assert {e.region for e in log.entries} == {"header"}


def test_wrap_and_shrink_cut_less_than_ellipsis(tmp_path):
    ell = len(_log(_narrow("ellipsis"), tmp_path).entries)
    wrap = len(_log(_narrow("wrap"), tmp_path, "w.pdf").entries)
    shr = len(_log(_narrow("shrink"), tmp_path, "s.pdf").entries)
    assert wrap <= ell and shr <= ell
    assert shr < ell  # 60 % of the size fits some titles that overflow at 100 %


def test_overflow_logs_nothing_for_weekly(tmp_path):
    assert not _log(_narrow("overflow"), tmp_path)


def _holiday_cfg(tmp_path, mode, **kw):
    f = tmp_path / "h.csv"
    f.write_text(f"month,day,name\n1,5,{HOLIDAY}\n", encoding="utf-8")
    return Config(
        year=2027,
        planners=["daily"],
        daily_months=[1],
        daily_holidays=True,
        holidays_file=f,
        header_text_fit=mode,
        **kw,
    )


def _jan5_page(cfg):
    plan = build_plan(cfg)
    return next(e.page_number for e in plan if str(e.ctx.get("date")) == "2027-01-05")


def test_daily_holiday_logged_in_every_mode(tmp_path):
    for mode in ("overflow", "ellipsis", "shrink", "wrap"):
        cfg = _holiday_cfg(tmp_path, mode)
        log = _log(cfg, tmp_path, f"{mode}.pdf")
        assert log.pages("header") == [_jan5_page(cfg)], mode
        assert [e.text for e in log.entries] == [HOLIDAY]


def test_default_a5_no_header_cut_in_ellipsis(tmp_path):
    cfg = Config(year=2027, header_text_fit="ellipsis", daily_holidays=False)
    assert not _log(cfg, tmp_path).pages("header")


def test_overflow_streams_equal_plain_cell(tmp_path):
    # Fitting text in "ellipsis" renders the same pages as "overflow" when nothing is cut.
    base = {
        "year": 2027,
        "planners": ["weekly", "daily"],
        "daily_months": [1],
        "daily_holidays": True,
    }
    a = Config(header_text_fit="overflow", **base)
    b = Config(header_text_fit="ellipsis", **base)
    ra = render_pages(a, build_plan(a), range(4))
    rb = render_pages(b, build_plan(b), range(4))
    assert ra == rb


OPTIONAL_IDS = (
    "goals",
    "important_dates",
    "todo",
    "projects",
    "budget",
    "habits",
    "monthly_review",
    "schedule",
    "holidays",
    "passwords",
)


@pytest.mark.parametrize("page_id", OPTIONAL_IDS)
def test_optional_header_cut_logged_with_agenda_page(page_id, tmp_path):
    from agenda.catalog import get_page

    cfg = _narrow("ellipsis", pages=[page_id])
    own = {e.page_number for e in build_plan(cfg) if e.page_class is get_page(page_id)}
    log = _log(cfg, tmp_path)
    assert own
    assert own <= set(log.pages("header"))
    assert {e.region for e in log.entries} == {"header"}


@pytest.mark.parametrize("page_id", OPTIONAL_IDS)
def test_optional_header_overflow_logs_nothing(page_id, tmp_path):
    assert not _log(_narrow("overflow", pages=[page_id], daily_holidays=False), tmp_path)
