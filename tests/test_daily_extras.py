import io
from datetime import date

from helpers import assert_in_safe_area
from pypdf import PdfReader

from agenda.day_extras import JOIN, builtin_quotes, truncate
from agenda.draw import HOLIDAY_STYLE, day_style_for, holiday_name_for
from agenda.config import Config
from agenda.exporter import add_page, new_document
from agenda.pages.core import Daily


def day_text(cfg: Config, d: date) -> str:
    page = Daily()
    ctx = next(c for c in page.instances(cfg) if c["date"] == d)
    pdf = new_document(cfg)
    page.draw(pdf, ctx, cfg, [add_page(pdf, cfg)])
    return PdfReader(io.BytesIO(bytes(pdf.output()))).pages[0].extract_text()


def day_pdf(cfg: Config, d: date) -> bytes:
    page = Daily()
    ctx = next(c for c in page.instances(cfg) if c["date"] == d)
    pdf = new_document(cfg)
    page.draw(pdf, ctx, cfg, [add_page(pdf, cfg)])
    return bytes(pdf.output())


def cfg_of(**kw) -> Config:
    return Config(year=2027, holiday_country="CR", language="es", **kw)


def test_old_output_without_extras():
    text = day_text(cfg_of(daily_holidays=False), date(2027, 1, 1))
    assert JOIN not in text
    for q in builtin_quotes("es"):
        assert q not in text


def test_default_shows_holiday_name():
    cfg = cfg_of()
    name = holiday_name_for(cfg)(date(2027, 1, 1))
    assert name and name in day_text(cfg, date(2027, 1, 1))
    assert JOIN not in day_text(cfg, date(2027, 1, 5))
    assert day_style_for(cfg)(date(2027, 1, 1)) is HOLIDAY_STYLE


def test_quotes_file_rotates(tmp_path):
    f = tmp_path / "q.txt"
    f.write_text("Alpha phrase\nBeta phrase\n", encoding="utf-8")
    cfg = cfg_of(daily_quotes=True, daily_quotes_file=f)
    assert "Alpha phrase" in day_text(cfg, date(2027, 1, 1))
    assert "Beta phrase" in day_text(cfg, date(2027, 1, 2))
    assert "Alpha phrase" in day_text(cfg, date(2027, 1, 3))


def test_builtin_quotes():
    cfg = cfg_of(daily_quotes=True)
    first = builtin_quotes("es")[0]
    text = " ".join(day_text(cfg, date(2027, 1, 1)).split())
    assert first[:15] in text


def test_extra_file(tmp_path):
    f = tmp_path / "e.txt"
    f.write_text("01-02 Dentist\n", encoding="utf-8")
    cfg = cfg_of(daily_extra_file=f)
    assert "Dentist" in day_text(cfg, date(2027, 1, 2))
    assert "Dentist" not in day_text(cfg, date(2027, 1, 1))


def test_all_extras_long_text_in_safe_area(tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("Q" * 300 + "\n", encoding="utf-8")
    e = tmp_path / "e.txt"
    e.write_text("01-01 " + "E" * 300 + "\n", encoding="utf-8")
    cfg = cfg_of(daily_quotes=True, daily_quotes_file=q, daily_extra_file=e)
    assert_in_safe_area(day_pdf(cfg, date(2027, 1, 1)), cfg)


def test_truncate():
    w = len
    assert truncate("abc", 5, w) == "abc"
    out = truncate("abcdefghij", 5, w)
    assert out.endswith("…") and len(out) <= 5
