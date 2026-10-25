import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda import tokens
from agenda.assembler import build_plan
from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.exporter import add_page, new_document
from agenda.grid import Grid
from agenda.i18n import Strings
from agenda.pages.optional import Passwords

SIZES = ("a5", "b6", "letter")


def test_registered_as_optional_passwords():
    assert get_page("passwords") is Passwords
    assert Passwords in pages_by_category("optional")
    assert (Passwords.category, Passwords.section) == ("optional", "optional")
    assert Passwords().instances(Config()) == [{}]


def test_count_and_negative():
    assert len(Passwords(count=2).instances(Config())) == 2
    assert Passwords(count=0).instances(Config()) == []
    with pytest.raises(ValueError):
        Passwords(count=-1)


def test_layout_rule():
    assert Passwords.layout(26) == 10
    assert Passwords.layout(27) == 10
    assert Passwords.layout(6) == 0
    assert Passwords.layout(0) == 0


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Passwords, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_warning_fits_box(lang, size):
    cfg = Config(language=lang, page_size=size)
    g = Grid.from_config(cfg)
    pdf = new_document(cfg)
    add_page(pdf, cfg)
    pdf.set_font("Inter", "", tokens.TYPE_SIZES_PT[1])
    icon = 2 * g.baseline
    width = g.safe.w - 3 * g.gutter - icon
    lines = pdf.multi_cell(
        width, g.baseline, Strings(lang)("passwords.warning"), dry_run=True, output="LINES"
    )
    assert len(lines) <= Passwords.WARN_ROWS - 1


def test_localized_text():
    for lang, title, warn, col in (
        ("es", "Contraseñas", "No escribas contraseñas reales", "Usuario"),
        ("en", "Passwords", "Do not write real passwords", "User"),
    ):
        page = PdfReader(io.BytesIO(render_page(Passwords, Config(language=lang)))).pages[0]
        text = " ".join(page.extract_text().split())
        assert title in text and warn in text and col in text


def test_plan_includes_passwords_only_when_listed():
    plan = build_plan(Config(pages=["passwords"]))
    assert [e.page_class for e in plan].count(Passwords) == 1
    assert Passwords not in [e.page_class for e in build_plan(Config())]
