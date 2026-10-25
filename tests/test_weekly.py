import io
from datetime import date

import pytest
from helpers import assert_in_safe_area, drawn_points
from pypdf import PdfReader

from agenda.calendar import iso_weeks_in_year
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.exporter import add_page, new_document
from agenda.grid import Grid, side_for_page
from agenda.i18n import Strings
from agenda.pages.core import Weekly


def render_spreads(cfg: Config) -> bytes:
    """Leading blank page 1 (a right page) so each Weekly spread starts on a left page."""
    page = Weekly()
    pdf = new_document(cfg)
    add_page(pdf, cfg)
    for ctx in page.instances(cfg):
        grids = [add_page(pdf, cfg) for _ in range(page.pages)]
        page.draw(pdf, ctx, cfg, grids)
    return bytes(pdf.output())


def test_registered_as_core_weekly():
    assert get_page("weekly") is Weekly
    assert Weekly in pages_by_category("core")
    assert (Weekly.section, Weekly.pages, Weekly.starts_on) == ("weekly", 2, "left")


@pytest.mark.parametrize(("year", "n"), [(2026, 53), (2027, 52), (2028, 52), (2020, 53)])
def test_instance_count(year, n):
    ctxs = Weekly().instances(Config(year=year))
    assert len(ctxs) == n == iso_weeks_in_year(year)
    assert [c["number"] for c in ctxs] == list(range(1, n + 1))


@pytest.mark.parametrize("week_start", ["monday", "sunday"])
def test_ctx_days_and_month(week_start):
    ctxs = Weekly().instances(Config(year=2026, week_start=week_start))
    assert all(len(c["days"]) == 7 for c in ctxs)
    wd = 0 if week_start == "monday" else 6
    assert all(c["days"][0].weekday() == wd for c in ctxs)
    assert ctxs[0]["days"][0] == date(2025, 12, 28 if week_start == "sunday" else 29)
    assert [c["month"] for c in ctxs] == sorted(c["month"] for c in ctxs)
    assert ctxs[0]["month"] == 1


def test_day_style_hook_default_is_none():
    assert Weekly.day_style(date(2026, 1, 1)) is None


@pytest.mark.parametrize("week_start", ["monday", "sunday"])
@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4", "letter"])
def test_spreads_render_left_right_in_safe_area(size, lang, week_start):
    cfg = Config(language=lang, page_size=size, week_start=week_start, year=2026)
    data = render_spreads(cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1 + 2 * 53
    s = Strings(lang)
    for i in range(53):
        left, right = 2 + 2 * i, 3 + 2 * i
        assert (side_for_page(left), side_for_page(right)) == ("left", "right")
        assert f"{s('week.number', n=i + 1)}" in reader.pages[left - 1].extract_text()
        assert s("notes.title") in reader.pages[right - 1].extract_text()
    assert_in_safe_area(data, cfg, allow_blank=True)


def test_year_boundary_days_shown():
    cfg = Config(year=2026)
    reader = PdfReader(io.BytesIO(render_spreads(cfg)))
    assert "Lunes 29" in reader.pages[1].extract_text()  # 29 Dec 2025 in week 1
    assert (
        "Diciembre 2025" in reader.pages[2].extract_text()
        or "diciembre" in reader.pages[2].extract_text().lower()
    )


def test_margins_flip_between_pages():
    cfg = Config(year=2026)
    pts = drawn_points(render_spreads(cfg))
    gl, gr = Grid.for_page(cfg, 2), Grid.for_page(cfg, 3)
    assert min(x for x, _ in pts[1]) == pytest.approx(gl.safe.x, abs=0.1)
    assert min(x for x, _ in pts[2]) == pytest.approx(gr.safe.x, abs=0.1)
    assert gl.safe.x != gr.safe.x
