"""config.yaml stays equivalent to the old flat sample; example files parse and validate."""

from datetime import date
from pathlib import Path

from agenda.config import Config
from agenda.configfile import load_yaml
from agenda.day_extras import load_dated, load_phrases

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
    quotes = load_phrases(ROOT / "examples/daily_quotes.csv")
    assert len(quotes) >= 7 and quotes[0].startswith("Small steps, taken daily")
    extra = load_dated(ROOT / "examples/daily_extra.csv", 2027)
    assert date(2027, 9, 14) in extra
    assert date(2028, 9, 14) not in load_dated(ROOT / "examples/daily_extra.csv", 2028)
    assert load_dated(ROOT / "examples/holidays.csv", 2027)[date(2027, 2, 14)] == "Team anniversary"


def test_config_with_example_files_validates():
    cfg = Config(
        year=2027,
        daily_quotes_file=ROOT / "examples/daily_quotes.csv",
        daily_extra_file=ROOT / "examples/daily_extra.csv",
        holidays_file=ROOT / "examples/holidays.csv",
    )
    assert cfg.holidays_file is not None
