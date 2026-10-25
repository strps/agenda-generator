from datetime import date

import pytest
from helpers import assert_in_safe_area, render_page

from agenda.config import Config
from agenda.draw import HOLIDAY_STYLE, WEEKEND_STYLE, day_style_for, holiday_name_for
from agenda.pages.core import Monthly, Weekly, Yearly


def test_known_cr_holiday():
    cfg = Config(year=2026)
    assert day_style_for(cfg)(date(2026, 12, 25)) == HOLIDAY_STYLE  # a Friday
    assert holiday_name_for(cfg)(date(2026, 12, 25))


def test_holiday_name_follows_language():
    es = holiday_name_for(Config(year=2026, language="es"))(date(2026, 12, 25))
    en = holiday_name_for(Config(year=2026, language="en"))(date(2026, 12, 25))
    assert es != en


def test_weekend_and_weekday():
    f = day_style_for(Config(year=2026))
    assert f(date(2026, 3, 7)) == WEEKEND_STYLE  # Saturday
    assert f(date(2026, 3, 8)) == WEEKEND_STYLE  # Sunday
    assert f(date(2026, 3, 9)) is None  # Monday


def test_weekend_independent_of_week_start():
    a = day_style_for(Config(year=2026, week_start="sunday"))
    assert a(date(2026, 3, 7)) == WEEKEND_STYLE and a(date(2026, 3, 9)) is None


def test_holiday_on_weekend_is_holiday():
    # 2026-08-15 is a Saturday and a CR holiday
    assert day_style_for(Config(year=2026))(date(2026, 8, 15)) == HOLIDAY_STYLE


def test_adjacent_year_dates():
    assert day_style_for(Config(year=2026))(date(2027, 1, 1)) == HOLIDAY_STYLE


def test_unknown_country_raises():
    with pytest.raises(ValueError):
        day_style_for(Config(year=2026, holiday_country="ZZ"))


@pytest.mark.parametrize("page", [Yearly, Monthly, Weekly])
def test_pages_render_in_safe_area(page):
    cfg = Config(year=2026)
    assert_in_safe_area(render_page(page, cfg), cfg, allow_blank=True)
