import io

import pytest
from helpers import assert_in_safe_area, drawn_points, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.pages.core import Contacts

SIZES = ("a5", "b6", "letter")


def test_registered_as_core_contacts():
    assert get_page("contacts") is Contacts
    assert Contacts in pages_by_category("core")
    assert (Contacts.section, Contacts.pages) == ("front_back", 1)


def test_instance_count():
    cfg = Config()
    assert len(Contacts().instances(cfg)) == 1
    assert len(Contacts(count=5).instances(cfg)) == 5
    assert Contacts(count=0).instances(cfg) == []
    with pytest.raises(ValueError):
        Contacts(count=-1)


@pytest.mark.parametrize("lang", ("es", "en"))
@pytest.mark.parametrize("size", SIZES)
def test_renders_inside_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(Contacts, cfg)
    assert len(PdfReader(io.BytesIO(data)).pages) == 1
    assert_in_safe_area(data, cfg)


def test_localized_text_and_many_entries():
    for lang, title in (("es", "Contactos"), ("en", "Contacts")):
        data = render_page(Contacts, Config(language=lang))
        assert title in PdfReader(io.BytesIO(data)).pages[0].extract_text()
        assert len(drawn_points(data)[0]) > 20
