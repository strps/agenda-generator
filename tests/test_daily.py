import io
from datetime import date

import pytest
from helpers import assert_in_safe_area
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.exporter import add_page, new_document
from agenda.i18n import Strings
from agenda.pages.core import Daily

SAMPLE = (0, 1, 58, 59, 180, 364)  # includes year start/end and a ~Feb 28/Mar 1 pair


def render_subset(cfg: Config, idx=SAMPLE) -> bytes:
    page = Daily()
    ctxs = page.instances(cfg)
    pdf = new_document(cfg)
    for i in idx:
        page.draw(pdf, ctxs[i], cfg, [add_page(pdf, cfg)])
    return bytes(pdf.output())


def test_registered_as_core_daily():
    assert get_page("daily") is Daily
    assert Daily in pages_by_category("core")
    assert (Daily.section, Daily.pages) == ("daily", 1)


@pytest.mark.parametrize(("year", "n"), [(2026, 365), (2028, 366), (2100, 365)])
def test_instance_count_and_order(year, n):
    ctxs = Daily().instances(Config(year=year))
    assert len(ctxs) == n
    dates = [c["date"] for c in ctxs]
    assert dates == sorted(dates)
    assert dates[0] == date(year, 1, 1) and dates[-1] == date(year, 12, 31)


def test_ctx_keys_iso_week():
    ctxs = Daily().instances(Config(year=2026))
    assert set(ctxs[0]) == {"date", "week", "iso_year"}
    assert (ctxs[0]["week"], ctxs[0]["iso_year"]) == (1, 2026)  # Thu 1 Jan 2026
    assert (ctxs[-1]["week"], ctxs[-1]["iso_year"]) == (53, 2026)
    c = Daily().instances(Config(year=2027))[0]  # Fri 1 Jan 2027 -> ISO week 53 of 2026
    assert (c["week"], c["iso_year"]) == (53, 2026)


def test_daily_months_not_applied():
    assert len(Daily().instances(Config(year=2026, daily_months=[1]))) == 365


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4", "letter"])
def test_render_valid_and_in_safe_area(size, lang):
    cfg = Config(language=lang, page_size=size, year=2026)
    data = render_subset(cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == len(SAMPLE)
    s = Strings(lang)
    text = reader.pages[0].extract_text()
    assert s("week.number", n=1) in text
    assert s("schedule") in text and s("priorities") in text and s("notes.title") in text
    assert s.month_name(1) in text and "06:00" in text
    assert_in_safe_area(data, cfg, x_slack=cfg.title_padding)


def test_header_localized():
    es = PdfReader(io.BytesIO(render_subset(Config(year=2026, language="es"), (0,))))
    en = PdfReader(io.BytesIO(render_subset(Config(year=2026, language="en"), (0,))))
    assert "Jueves 1 de" in es.pages[0].extract_text()
    assert "Thursday, " in en.pages[0].extract_text()


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["a5", "b6"])
def test_section_titles_have_top_margin(size, lang, monkeypatch):
    from agenda import tokens
    from agenda.pdfdoc import AgendaPDF

    calls: list[tuple[str, float, float]] = []
    lines: list[tuple] = []
    orig = AgendaPDF.cell
    orig_line = AgendaPDF.line

    def line_spy(self, *a, **k):
        lines.append(a)
        return orig_line(self, *a, **k)

    monkeypatch.setattr(AgendaPDF, "line", line_spy)

    def spy(self, w=None, h=None, text="", *args, **kwargs):
        calls.append((text, self.get_y(), h))
        return orig(self, w, h, text, *args, **kwargs)

    monkeypatch.setattr(AgendaPDF, "cell", spy)
    cfg = Config(language=lang, page_size=size, year=2026)
    page = Daily()
    pdf = new_document(cfg)
    g = add_page(pdf, cfg)
    page.draw(pdf, page.instances(cfg)[0], cfg, [g])

    s = Strings(lang)
    gap = tokens.SPACING[1]
    half = g.rows // 2
    n_hours = min(cfg.daily_hour_end - cfg.daily_hour_start + 1, g.rows - 1)
    per = (g.rows - 1) // n_hours
    expected = {
        s("schedule"): (g.header.y + g.header.h + gap, 0),
        s("priorities"): (g.header.y + g.header.h + gap, 0),
        s("notes.title"): (g.row(half) + gap, half),
    }
    for text, (min_y, r0) in expected.items():
        (_, y, h) = next(c for c in calls if c[0] == text)
        assert y >= min_y - 1e-6
        assert y + h <= g.row(r0 + 1) + 1e-6
    hours = [c for c in calls if len(c[0]) == 5 and c[0].endswith(":00")]
    assert len(hours) == n_hours
    assert per >= 1
    # Unchanged by the label gap: one rule per hour, then write-in lines under each title.
    write_in = (half - 2 + 1) + (g.rows - (half + 2) + 1)
    assert len(lines) == n_hours + write_in
