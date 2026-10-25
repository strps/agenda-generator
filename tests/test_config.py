import datetime

import pytest
from pydantic import ValidationError

from agenda.config import Config


def test_defaults():
    c = Config()
    assert c.page_size == "half_letter"
    assert c.orientation == "portrait"
    assert (c.booklet_size, c.booklet_unit, c.booklet_folded) == (5, "sheets", True)
    assert c.pages_per_booklet == 20
    assert c.planners == ["weekly", "daily"]
    assert c.daily_months == list(range(1, 13))
    assert c.num_booklets == "auto"
    assert c.pages is None
    assert c.year == datetime.date.today().year
    assert (c.week_start, c.language, c.holiday_country) == ("monday", "es", "CR")
    assert (c.inner_margin, c.outer_margin) == (15, 10)
    assert (c.notes_pattern, c.theme) == ("dotted", "minimal")
    assert c.imposition is False and c.crop_marks is False
    assert str(c.output) == "agenda.pdf"
    assert c.bleed == 3 and c.separate_covers is False


def test_default_lists_not_shared():
    a, b = Config(), Config()
    a.planners.append("weekly")
    assert b.planners == ["weekly", "daily"]


@pytest.mark.parametrize("size", ["a5", "A4", "139.7x215.9", "100 X 150"])
def test_page_size_ok(size):
    assert Config(page_size=size)


@pytest.mark.parametrize("size", ["tabloid", "10x", "axb", ""])
def test_page_size_bad(size):
    with pytest.raises(ValidationError):
        Config(page_size=size)


def test_daily_months_spec():
    assert Config(daily_months="1-3,6").daily_months == [1, 2, 3, 6]
    with pytest.raises(ValidationError):
        Config(daily_months=[0, 13])
    with pytest.raises(ValidationError):
        Config(daily_months="5-2")


@pytest.mark.parametrize(
    "kw",
    [
        {"orientation": "square"},
        {"week_start": "friday"},
        {"language": "fr"},
        {"notes_pattern": "dots"},
        {"planners": ["monthly"]},
        {"inner_margin": -1},
        {"booklet_size": 0},
        {"num_booklets": 0},
        {"num_booklets": "many"},
        {"unknown": 1},
    ],
)
def test_invalid(kw):
    with pytest.raises(ValidationError):
        Config(**kw)


def test_imposition_requires_folded():
    with pytest.raises(ValidationError):
        Config(imposition=True, booklet_folded=False)
    assert Config(imposition=True).imposition


def test_pages_unit_multiple_of_four():
    with pytest.raises(ValidationError):
        Config(booklet_unit="pages", booklet_size=18)
    assert Config(booklet_unit="pages", booklet_size=24).pages_per_booklet == 24
    assert Config(booklet_unit="pages", booklet_size=18, booklet_folded=False)


def test_country_and_num_booklets():
    assert Config(holiday_country="mx").holiday_country == "MX"
    assert Config(num_booklets=3).num_booklets == 3


def test_pad_with_validated_against_catalog():
    assert Config().pad_with == "notes"
    assert Config(pad_with=" weekly ").pad_with == "weekly"
    with pytest.raises(ValidationError, match="unknown page id"):
        Config(pad_with="nope")


def test_imposition_error_message():
    with pytest.raises(ValidationError, match="imposition requires booklet_folded"):
        Config(imposition=True, booklet_folded=False)
    assert Config(imposition=False, booklet_folded=False)


def test_folded_pages_message_and_valid_sizes():
    with pytest.raises(ValidationError, match="multiple of 4"):
        Config(booklet_unit="pages", booklet_size=6)
    for n in (4, 8, 40):
        assert Config(booklet_unit="pages", booklet_size=n).pages_per_booklet == n
    for n in (1, 3, 5):  # sheets: always fine
        assert Config(booklet_size=n).pages_per_booklet % 4 == 0


def test_flat_pages_multiple_of_two():
    with pytest.raises(ValidationError, match="multiple of 2"):
        Config(booklet_unit="pages", booklet_size=7, booklet_folded=False)
    assert Config(booklet_unit="pages", booklet_size=6, booklet_folded=False)


def test_validate_assignment_rules():
    c = Config(imposition=True)
    with pytest.raises(ValidationError):
        c.booklet_folded = False
    # NB: pydantic does not roll back a failed assignment; the object is left invalid
    c2 = Config(booklet_unit="pages", booklet_size=8)
    with pytest.raises(ValidationError):
        c2.booklet_size = 6
    c3 = Config(booklet_unit="pages", booklet_size=8)
    c3.booklet_size = 12
    assert c3.pages_per_booklet == 12
