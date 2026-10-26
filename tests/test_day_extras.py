from datetime import date

import pytest
from pydantic import ValidationError

from agenda import day_extras as D
from agenda import templates
from agenda.config import Config
from agenda.gui import settings_model as M


def test_read_lines_skips_blank_and_comments(tmp_path):
    f = tmp_path / "x.txt"
    f.write_text("  # c\n\n  12-25 Xmas  \n\t\nplain\n", encoding="utf-8")
    assert D.read_lines(f) == ["12-25 Xmas", "plain"]


def test_read_lines_missing_names_path(tmp_path):
    with pytest.raises(ValueError, match="nope.txt"):
        D.read_lines(tmp_path / "nope.txt")


def test_parse_dated():
    lines = ["12-25 Xmas", "2027-03-01;Trip", "12-25 Family"]
    got = D.parse_dated(lines, 2027)
    assert got == {date(2027, 12, 25): "Xmas · Family", date(2027, 3, 1): "Trip"}
    assert date(2028, 3, 1) not in D.parse_dated(lines, 2028)
    assert D.parse_dated(["2027-03-01\tTab"], 2027) == {date(2027, 3, 1): "Tab"}
    for bad in ("13-01 x", "no date"):
        with pytest.raises(ValueError, match="line 2"):
            D.parse_dated(["01-01 ok", bad], 2027)


def test_quote_for_and_builtin():
    q = [f"q{i}" for i in range(12)]
    assert D.quote_for(date(2027, 1, 1), q) == "q0"
    assert D.quote_for(date(2027, 1, 13), q) == "q0"
    assert D.quote_for(date(2027, 5, 5), q) == D.quote_for(date(2027, 5, 5), q)
    assert D.quote_for(date(2027, 1, 1), []) is None
    en, es = D.builtin_quotes("en"), D.builtin_quotes("es")
    assert len(en) == 12 and all(en) and en != es


def test_config_defaults_and_validation(tmp_path):
    c = Config()
    assert c.daily_holidays is True and c.daily_quotes is False
    assert c.daily_quotes_file is None and c.daily_extra_file is None and c.holidays_file is None
    with pytest.raises(ValidationError, match="daily_quotes_file"):
        Config(daily_quotes_file=tmp_path / "missing.txt")
    bad = tmp_path / "h.txt"
    bad.write_text("01-01 ok\nnot a date\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="holidays_file"):
        Config(holidays_file=bad)
    good = tmp_path / "g.txt"
    good.write_text("01-02 Mine\n", encoding="utf-8")
    assert Config(holidays_file=good, daily_extra_file=good).holidays_file == good
    q = tmp_path / "q.txt"
    q.write_text("free text phrase\n", encoding="utf-8")
    assert Config(daily_quotes_file=q).daily_quotes_file == q


def test_sections_and_kinds():
    assert templates.group_of("holidays_file") == templates.GLOBAL
    assert templates.group_of("daily_quotes_file") == "daily"
    kinds = {s.name: s.kind for s in M.field_specs()}
    for n in ("daily_quotes_file", "daily_extra_file", "holidays_file"):
        assert kinds[n] == M.OPT_PATH
    assert kinds["output"] == M.PATH


def test_yaml_roundtrip_with_paths(tmp_path):
    f = tmp_path / "h.txt"
    f.write_text("01-02 Mine\n", encoding="utf-8")
    cfg = Config(holidays_file=f, daily_quotes_file=f, daily_quotes=True)
    out = tmp_path / "c.yaml"
    M.save_yaml(cfg, out)
    assert Config(**M.load_values(out)) == cfg
