import string

import pytest

from agenda import uitext
from agenda.uitext import en, es


def _fields(text):
    return {name for _, name, _, _ in string.Formatter().parse(text) if name is not None}


def test_es_keys_match_en():
    assert set(es.MESSAGES) == set(en.MESSAGES)
    assert uitext.keys() == frozenset(en.MESSAGES)


def test_placeholders_match():
    for key, text in en.MESSAGES.items():
        assert _fields(text) == _fields(es.MESSAGES[key]), key


@pytest.mark.parametrize(
    "pref, locale, expected",
    [
        ("system", "es_PE.UTF-8", "es"),
        ("system", "fr_FR", "en"),
        ("en", "es_ES", "en"),
        ("es", "en_US", "es"),
        (None, None, "en"),
        (None, "es", "es"),
    ],
)
def test_resolve_language(pref, locale, expected):
    assert uitext.resolve_language(pref, locale) == expected


def test_system_language_precedence():
    env = {"AGENDA_UI_LANG": "en", "LC_ALL": "es_ES", "LC_MESSAGES": "es", "LANG": "es"}
    assert uitext.system_language(env) == "en"
    assert uitext.system_language({"LC_ALL": "en_US", "LC_MESSAGES": "es", "LANG": "es"}) == "en"
    assert uitext.system_language({"LC_MESSAGES": "es_MX", "LANG": "en_US"}) == "es"
    assert uitext.system_language({"LANG": "es_ES.UTF-8"}) == "es"
    assert uitext.system_language({}) == "en"


def test_invalid_env_falls_back_to_locale():
    assert uitext.system_language({"AGENDA_UI_LANG": "xx", "LANG": "es_ES"}) == "es"
    assert uitext.system_language({"AGENDA_UI_LANG": "xx"}) == "en"


def test_tr_languages_and_errors():
    uitext.set_language("es")
    assert uitext.tr("common.ok") == es.MESSAGES["common.ok"]
    uitext.set_language("en")
    assert uitext.tr("common.ok") == "OK"
    with pytest.raises(KeyError, match="no.such.key"):
        uitext.tr("no.such.key")
    with pytest.raises(ValueError):
        uitext.set_language("fr")


def test_tr_falls_back_to_english(monkeypatch):
    monkeypatch.setitem(en.MESSAGES, "test.only_en", "Hi {name}")
    uitext.set_language("es")
    assert uitext.tr("test.only_en", name="Ana") == "Hi Ana"


def test_conftest_forces_english():
    assert uitext.get_language() == "en"
