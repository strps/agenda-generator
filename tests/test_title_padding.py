import pytest
from fpdf import FPDF
from helpers import render_page

from agenda.config import Config
from agenda.draw import fill_title_band


class _Spy(FPDF):
    def __init__(self):
        super().__init__()
        self.rects = []

    def rect(self, x, y, w, h, style=None, *args, **kwargs):
        self.rects.append((x, y, w, h, style))


def test_band_grows_outward_by_pad():
    pdf = _Spy()
    fill_title_band(pdf, 10, 20, 100, 12, (1, 2, 3), 2.5)
    assert pdf.rects == [(7.5, 20, 105, 12, "F")]


def test_zero_pad_is_flush():
    pdf = _Spy()
    fill_title_band(pdf, 10, 20, 100, 12, (1, 2, 3), 0)
    assert pdf.rects == [(10, 20, 100, 12, "F")]


def test_config_default_and_bounds():
    assert Config().title_padding == 2.0
    with pytest.raises(ValueError):
        Config(title_padding=-1)


@pytest.mark.parametrize("page", ["Daily", "Weekly"])
def test_pages_pass_the_padding(monkeypatch, page):
    from agenda.pages import core

    calls = []
    monkeypatch.setattr(core, "fill_title_band", lambda *a: calls.append(a))
    cfg = Config(year=2026, planners=["weekly", "daily"], daily_months=[1], title_padding=4.0)
    render_page(getattr(core, page), cfg)
    # January has weekends, so filled titles are drawn, all with the configured padding
    assert calls and all(c[-1] == 4.0 for c in calls)
