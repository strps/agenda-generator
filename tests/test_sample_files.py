"""config.yaml stays equivalent to the old flat sample; example files parse and validate."""

from datetime import date
from pathlib import Path

from agenda.config import Config
from agenda.configfile import load_yaml
from agenda.day_extras import parse_dated, read_lines

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    "cover",
    "personal_info",
    "yearly",
    "monthly",
    "weekly",
    "habits",
    "health",
    "qr",
    "notes",
    "contacts",
    "back_cover",
]


def test_config_yaml_matches_flat_sample():
    expected = Config(
        page_size="half_letter",
        year=2027,
        week_start="monday",
        language="es",
        holiday_country="CR",
        booklet_size=5,
        booklet_unit="sheets",
        booklet_folded=True,
        planners=["weekly", "daily"],
        notes_pattern="dotted",
        pad_with="notes",
        pages=PAGES,
    )
    assert Config(**load_yaml(ROOT / "config.yaml")) == expected


def test_example_files_parse():
    assert len(read_lines(ROOT / "examples/daily_quotes.txt")) >= 7
    extra = parse_dated(read_lines(ROOT / "examples/daily_extra.txt"), 2027)
    assert date(2027, 9, 14) in extra
    assert parse_dated(read_lines(ROOT / "examples/holidays.txt"), 2027)


def test_config_with_example_files_validates():
    cfg = Config(
        year=2027,
        daily_quotes_file=ROOT / "examples/daily_quotes.txt",
        daily_extra_file=ROOT / "examples/daily_extra.txt",
        holidays_file=ROOT / "examples/holidays.txt",
    )
    assert cfg.holidays_file is not None
