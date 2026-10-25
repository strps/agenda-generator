import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.i18n import Strings
from agenda.pages.core import PersonalInfo

KEYS = ["name", "address", "phone", "email", "emergency", "blood_type"]


def test_registered_as_core_front_back():
    assert get_page("personal_info") is PersonalInfo
    assert PersonalInfo in pages_by_category("core")
    assert (PersonalInfo.category, PersonalInfo.section, PersonalInfo.pages) == (
        "core",
        "front_back",
        1,
    )


def test_single_instance():
    assert PersonalInfo().instances(Config()) == [{}]


@pytest.mark.parametrize("lang", ["es", "en"])
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4"])
def test_renders_valid_pdf_with_labels_in_safe_area(lang, size):
    cfg = Config(language=lang, page_size=size)
    data = render_page(PersonalInfo, cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = " ".join(reader.pages[0].extract_text().split())
    s = Strings(lang)
    for k in ["title", *KEYS]:
        assert s(f"personal.{k}") in text
    assert_in_safe_area(data, cfg)
