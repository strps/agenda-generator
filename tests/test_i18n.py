import pytest

from agenda import i18n
from agenda.config import Config


def test_key_parity():
    assert set(i18n.STRINGS["es"]) == set(i18n.STRINGS["en"])
    assert set(i18n.STRINGS) == set(i18n.LANGUAGES)


def test_format_fields_match_between_languages():
    import string

    f = string.Formatter()

    def fields(s):
        return {x[1] for x in f.parse(s) if x[1]}

    for key, es in i18n.STRINGS["es"].items():
        en = i18n.STRINGS["en"][key]
        assert fields(es) == fields(en), key


def test_config_language_supported():
    assert Config().language in i18n.LANGUAGES


def test_t_formatting():
    assert i18n.t("week.number", "es", n=3) == "Semana 3"
    assert i18n.t("week.number", "en", n=3) == "Week 3"
    assert i18n.t("cover.year", "en", year=2027) == "Planner 2027"
    assert i18n.t("notes.title", "es") == "Notas"


def test_missing_key_and_language():
    with pytest.raises(KeyError, match="nope"):
        i18n.t("nope", "es")
    with pytest.raises(ValueError):
        i18n.t("notes.title", "fr")
    with pytest.raises(ValueError):
        i18n.Strings("fr")


def test_months():
    assert i18n.month_name(1, "es") == "Enero"
    assert i18n.month_name(12, "en", short=True) == "Dec"
    for lang in i18n.LANGUAGES:
        assert len({i18n.month_name(m, lang) for m in range(1, 13)}) == 12
        assert all(len(i18n.month_name(m, lang, True)) == 3 for m in range(1, 13))
    for bad in (0, 13):
        with pytest.raises(ValueError):
            i18n.month_name(bad, "es")


def test_weekdays_monday_and_sunday():
    assert i18n.weekday_names("es")[0] == "Lunes"
    assert i18n.weekday_names("es")[-1] == "Domingo"
    assert i18n.weekday_names("en", "sunday", "short") == [
        "Sun",
        "Mon",
        "Tue",
        "Wed",
        "Thu",
        "Fri",
        "Sat",
    ]
    assert i18n.weekday_names("es", "sunday", "letter") == list("DLMXJVS")
    for lang in i18n.LANGUAGES:
        for form in ("full", "short", "letter"):
            assert len(i18n.weekday_names(lang, "monday", form)) == 7
    with pytest.raises(ValueError):
        i18n.weekday_names("es", "friday")
    with pytest.raises(ValueError):
        i18n.weekday_names("es", form="tiny")


def test_strings_and_weekday_name():
    s = i18n.Strings("en")
    assert s("week.number", n=2) == "Week 2"
    assert s.month_name(3) == "March"
    assert s.weekday_names("sunday")[0] == "Sunday"
    assert i18n.weekday_name(2, "es", "short") == "Mié"
