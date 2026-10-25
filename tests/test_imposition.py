import pytest

from agenda.gui.preview_model import sheet_rows
from agenda.imposition import imposition_order


def test_eight_pages():
    assert imposition_order(8) == [(8, 1), (2, 7), (6, 3), (4, 5)]


def test_four_and_empty():
    assert imposition_order(4) == [(4, 1), (2, 3)]
    assert imposition_order(0) == []


@pytest.mark.parametrize("n", [1, 2, 6, 10, -4])
def test_rejects_non_multiple_of_four(n):
    with pytest.raises(ValueError, match="multiple of 4"):
        imposition_order(n)


@pytest.mark.parametrize("n", [4, 8, 12, 32, 48])
def test_agrees_with_preview_sheet_mode(n):
    sides = imposition_order(n)
    booklet_of = [1] * n
    for s in range(n // 4):
        rows = sheet_rows(s * 2, booklet_of)  # plan index 2s is page 2s+1 of sheet s+1
        assert [tuple(i + 1 for i in r) for r in rows] == sides[2 * s : 2 * s + 2]


# ---- 2-up placement

import io

from pypdf import PdfReader

from agenda.config import Config
from agenda.exporter import export_agenda
from agenda.imposition import (
    MM_PT,
    choose_sheet,
    impose_booklets,
    place_two_up,
    placement_scale,
)


def _pdf(n, w=139.7, h=215.9):
    from fpdf import FPDF

    pdf = FPDF(unit="mm", format=(w, h))
    pdf.set_font("Helvetica", size=20)
    for i in range(1, n + 1):
        pdf.add_page()
        pdf.text(10, 20, f"P{i}")
    return bytes(pdf.output())


def _texts(data):
    return [p.extract_text().split() for p in PdfReader(io.BytesIO(data)).pages]


def test_half_letter_fills_letter_landscape_exactly():
    s, left, right = place_two_up(139.7, 215.9, 279.4, 215.9)
    assert s == 1 and left == (0, 0) and right == pytest.approx((139.7, 0))


def test_a5_fills_a4():
    assert choose_sheet(148, 210) == (297.0, 210.0)
    assert choose_sheet(139.7, 215.9) == (279.4, 215.9)


def test_small_page_centred_not_enlarged():
    s, left, right = place_two_up(100, 100, 280, 200)
    assert s == 1 and left == (20, 50) and right == (160, 50)


def test_large_page_scaled_to_fit():
    assert placement_scale(200, 300, 280, 200) == pytest.approx(200 / 300)
    s, left, right = place_two_up(200, 300, 280, 200)
    assert left[0] + 200 * s <= 140 + 1e-9 and right[0] >= 140


def test_impose_booklets_order_and_sheet_size():
    out = impose_booklets(_pdf(8), [1] * 8)
    reader = PdfReader(io.BytesIO(out))
    assert len(reader.pages) == 4
    assert float(reader.pages[0].mediabox.width) == pytest.approx(279.4 * MM_PT, abs=0.1)
    assert _texts(out) == [["P8", "P1"], ["P2", "P7"], ["P6", "P3"], ["P4", "P5"]]


def test_impose_booklets_positions_left_right():
    out = impose_booklets(_pdf(4), [1] * 4)
    page = PdfReader(io.BytesIO(out)).pages[0]
    xs = {}
    page.extract_text(
        visitor_text=lambda t, cm, tm, fd, fs: (
            xs.update({t.strip(): cm[4] + tm[4] * cm[0]}) if t.strip() else None
        )
    )
    assert xs["P4"] < page.mediabox.width / 2 < xs["P1"]


def test_impose_pads_partial_booklet_and_keeps_plain_pages():
    out = impose_booklets(_pdf(7), [None, 1, 1, 1, None, None, None])
    # cover, 3 booklet pages padded to 4 -> 2 sides, then 3 trailing plain pages
    texts = _texts(out)
    assert texts[0] == ["P1"] and len(texts) == 1 + 2 + 3
    assert texts[1] == ["P2"] and texts[2] == ["P3", "P4"]  # sides (blank, P2), (P3, P4)


def test_export_imposed_has_one_sheet_side_per_four_pages(tmp_path):
    base = Config(year=2025, booklet_size=2, num_booklets=1)
    plain = export_agenda(base, tmp_path / "a.pdf")
    imp = export_agenda(base.model_copy(update={"imposition": True}), tmp_path / "b.pdf")
    n = len(PdfReader(plain).pages)
    assert len(PdfReader(imp).pages) == n // 2
    assert float(PdfReader(imp).pages[0].mediabox.width) == pytest.approx(279.4 * MM_PT, abs=0.1)


def test_normal_export_unchanged_by_imposition_support(tmp_path):
    from agenda.assembler import build_plan
    from agenda.exporter import render_pages

    cfg = Config(year=2025, booklet_size=2, num_booklets=1)
    out = export_agenda(cfg, tmp_path / "a.pdf")
    plan = build_plan(cfg)
    assert _texts(out.read_bytes()) == _texts(render_pages(cfg, plan, range(len(plan))))
