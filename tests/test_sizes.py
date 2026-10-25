import pytest

from agenda.config import Config
from agenda.sizes import SIZES, parse_size, resolve_size


def test_five_named_sizes():
    assert set(SIZES) == {"half_letter", "a5", "letter", "a4", "b6"}
    assert parse_size("Half_Letter") == (139.7, 215.9)


def test_custom():
    assert parse_size("150x200") == (150, 200)
    assert parse_size(" 150.5 X 200 ") == (150.5, 200)


@pytest.mark.parametrize("bad", ["", "foo", "150", "150x", "-1x200", "10x200", "2000x200", "1x2x3"])
def test_invalid(bad):
    with pytest.raises(ValueError):
        parse_size(bad)


def test_orientation():
    assert resolve_size("a5") == (148, 210)
    assert resolve_size("a5", "landscape") == (210, 148)
    assert resolve_size("200x100", "portrait") == (100, 200)
    assert resolve_size("100x200", "landscape") == (200, 100)
    with pytest.raises(ValueError):
        resolve_size("a5", "diagonal")


def test_config_integration():
    assert Config(page_size="A4").page_dimensions == (210, 297)
    assert Config(page_size="150x200", orientation="landscape").page_dimensions == (200, 150)
    with pytest.raises(ValueError):
        Config(page_size="5x5")
