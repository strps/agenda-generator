"""Footer text fit (footer_text_fit) and cut logging through export_agenda / render_pages."""

from __future__ import annotations

import io
from datetime import date

import pytest
from pypdf import PdfReader

from agenda.assembler import build_plan
from agenda.config import Config
from agenda.exporter import export_agenda, render_pages
from agenda.textfit import CutLog

LONG = "Very long phrase " * 12
MEDIUM = (
    "A moderately long daily phrase that needs more room than one line of the footer can give it, "
    "so it has to go on a second line"
)


def _cfg_one_long(tmp_path, phrase, mode):
    # Quote rotates by day of year: day 1 gets the first line, day 2 the second, ...
    f = tmp_path / "q.txt"
    f.write_text(f"Hi\n{phrase}\nHi\nHi\n", encoding="utf-8")
    return Config(
        year=2027,
        planners=["daily"],
        daily_months=[1],
        daily_quotes=True,
        daily_quotes_file=f,
        daily_holidays=False,
        footer_text_fit=mode,
    )


def _long_day_pages(cfg):
    plan = build_plan(cfg)
    return plan, [
        i
        for i, e in enumerate(plan)
        if e.ctx.get("date") is not None and (e.ctx["date"] - date(2027, 1, 2)).days % 4 == 0
    ]


def test_ellipsis_logs_exact_pages(tmp_path):
    cfg = _cfg_one_long(tmp_path, LONG, "ellipsis")
    plan, idx = _long_day_pages(cfg)
    assert idx
    log = CutLog()
    out = export_agenda(cfg, tmp_path / "a.pdf", cuts=log)
    expected = sorted(plan[i].page_number for i in idx if plan[i].ctx["date"].month == 1)
    assert log.pages("footer") == expected
    assert {e.region for e in log.entries} == {"footer"}
    page = PdfReader(str(out)).pages[expected[0] - 1].extract_text()
    assert "…" in page


def _runs(pdf_bytes, page_no):
    ys = []

    def visitor(text, cm, tm, font_dict, font_size):
        if text.strip():
            ys.append((round(tm[5] * 1 + cm[5], 1), text.strip()))

    PdfReader(io.BytesIO(pdf_bytes)).pages[page_no].extract_text(visitor_text=visitor)
    return ys


def test_wrap_two_lines_not_logged(tmp_path):
    cfg = _cfg_one_long(tmp_path, MEDIUM, "wrap")
    plan, idx = _long_day_pages(cfg)
    log = CutLog()
    out = export_agenda(cfg, tmp_path / "w.pdf", cuts=log)
    assert not log
    n = plan[idx[0]].page_number - 1
    ys = {
        y
        for y, t in _runs(out.read_bytes(), n)
        if "phrase" in t or "give" in t or "footer" in t or "second" in t
    }
    assert len(ys) == 2
    assert "…" not in PdfReader(str(out)).pages[n].extract_text()


def test_shrink_no_ellipsis_not_logged(tmp_path):
    cfg = _cfg_one_long(tmp_path, MEDIUM, "shrink")
    plan, idx = _long_day_pages(cfg)
    log = CutLog()
    out = export_agenda(cfg, tmp_path / "s.pdf", cuts=log)
    assert not log
    n = plan[idx[0]].page_number - 1
    text = PdfReader(str(out)).pages[n].extract_text()
    assert "…" not in text
    assert "second line" in text


@pytest.mark.parametrize("mode", ["ellipsis"])
def test_render_pages_logs_same_agenda_page(tmp_path, mode):
    cfg = _cfg_one_long(tmp_path, LONG, mode)
    plan, idx = _long_day_pages(cfg)
    full = CutLog()
    export_agenda(cfg, tmp_path / "f.pdf", cuts=full)
    i = next(i for i in idx if plan[i].page_number in full.pages())
    part = CutLog()
    render_pages(cfg, plan, [i], cuts=part)
    assert part.pages() == [plan[i].page_number]
    assert plan[i].page_number in full.pages()
    # export_agenda(pages=) too
    via = CutLog()
    export_agenda(cfg, tmp_path / "p.pdf", pages=[plan[i].page_number], cuts=via)
    assert via.pages() == part.pages()


def test_default_without_cuts_collects_nothing(tmp_path):
    cfg = _cfg_one_long(tmp_path, "short", "ellipsis")
    log = CutLog()
    export_agenda(cfg, tmp_path / "d.pdf", cuts=log)
    assert not log
