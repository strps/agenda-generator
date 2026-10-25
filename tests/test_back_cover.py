import io

import pytest
from helpers import assert_in_safe_area, render_page
from pypdf import PdfReader

from agenda.catalog import get_page, pages_by_category
from agenda.config import Config
from agenda.pages.core import BackCover


def test_registered_as_core_front_back():
    assert get_page("back_cover") is BackCover
    assert BackCover in pages_by_category("core")
    assert (BackCover.category, BackCover.section, BackCover.pages) == ("core", "front_back", 1)


def test_single_instance():
    assert BackCover().instances(Config()) == [{}]


@pytest.mark.parametrize(
    "lang,line", [("es", "Que cada día cuente"), ("en", "Make every day count")]
)
@pytest.mark.parametrize("size", ["half_letter", "a5", "b6", "a4"])
def test_renders_valid_pdf_in_safe_area(lang, line, size):
    cfg = Config(language=lang, page_size=size, year=2027)
    data = render_page(BackCover, cfg)
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "2027" in text and line in text
    assert_in_safe_area(data, cfg)
