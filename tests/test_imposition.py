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


# ---------------------------------------------------------------- bleed and crop marks


def _strokes(page) -> int:
    return page.get_contents().get_data().replace(b"\n", b" ").count(b"l S")


def test_crop_mark_segments_geometry():
    from agenda.imposition import crop_mark_segments

    segs = crop_mark_segments(10, 20, 100, 50, bleed=3, length=4)
    assert len(segs) == 8 and len(set(segs)) == 8
    assert (7, 20, 3, 20) in segs  # bottom-left, horizontal, pointing left
    assert (10, 17, 10, 13) in segs  # bottom-left, vertical, pointing down
    assert (113, 70, 117, 70) in segs and (110, 73, 110, 77) in segs  # top-right
    # no mark touches the trim box or the bleed zone
    for x1, y1, x2, y2 in segs:
        for x, y in ((x1, y1), (x2, y2)):
            assert not (7 < x < 113 and 17 < y < 73) or x in (10, 110) or y in (20, 70)


def test_inset_shrinks_pages_and_keeps_them_clear_of_the_edge():
    from agenda.imposition import marks_inset, place_two_up

    s0, *_ = place_two_up(139.7, 215.9, 279.4, 215.9)
    inset = marks_inset(3)
    s, (lx, ly), (rx, _) = place_two_up(139.7, 215.9, 279.4, 215.9, inset)
    assert s < s0 and ly >= inset - 1e-9 and lx >= inset - 1e-9
    assert rx + 139.7 * s + inset <= 279.4 + 1e-9


def test_impose_with_marks_draws_lines_and_keeps_order():
    plain = impose_booklets(_pdf(4), [1] * 4)
    marked = impose_booklets(_pdf(4), [1] * 4, bleed_mm=3)
    r = PdfReader(io.BytesIO(marked))
    assert _texts(marked) == _texts(plain)
    assert _strokes(r.pages[0]) == 16  # 8 marks x 2 pages on a full side
    assert _strokes(PdfReader(io.BytesIO(plain)).pages[0]) == 0


def test_export_with_crop_marks(tmp_path):
    base = Config(year=2025, booklet_size=2, num_booklets=1, imposition=True)
    out = export_agenda(base.model_copy(update={"crop_marks": True}), tmp_path / "m.pdf")
    assert _strokes(PdfReader(out).pages[0]) > 0


def test_crop_marks_require_imposition():
    with pytest.raises(ValueError, match="crop_marks requires imposition"):
        Config(crop_marks=True)


# ---------------------------------------------------------------- properties and the Done-when

from helpers import PT, drawn_points

from agenda.grid import side_for_page

_SIZES = list(range(4, 201, 4))


@pytest.mark.parametrize("n", _SIZES)
def test_order_every_page_once_and_pairs_sum_to_n_plus_1(n):
    sides = imposition_order(n)
    assert len(sides) == n // 2
    assert sorted(p for side in sides for p in side) == list(range(1, n + 1))
    assert all(a + b == n + 1 for a, b in sides)


@pytest.mark.parametrize("n", _SIZES)
def test_order_front_back_alternation(n):
    # In a folded booklet every side has an even page on the left (verso) and an odd page on the
    # right (recto), the same rule the grid uses for the binding margin.
    for left, right in imposition_order(n):
        assert left % 2 == 0 and right % 2 == 1
        assert side_for_page(left) == "left" and side_for_page(right) == "right"
    # sheet s: front is (n-2s+2, 2s-1), back (2s, n-2s+1)
    for s in range(1, n // 4 + 1):
        assert imposition_order(n)[2 * s - 2] == (n - 2 * s + 2, 2 * s - 1)
        assert imposition_order(n)[2 * s - 1] == (2 * s, n - 2 * s + 1)


def _text_xs(page):
    """Map text token -> x of its origin in points."""
    xs = {}

    def visit(t, cm, tm, fd, fs):
        if t.strip():
            xs[t.strip()] = cm[4] + tm[4] * cm[0]

    page.extract_text(visitor_text=visit)
    return xs


@pytest.mark.parametrize("n", [4, 8, 12, 20, 40])
@pytest.mark.parametrize("bleed", [None, 3])
def test_pdf_sides_hold_expected_pages_in_their_half(n, bleed):
    out = impose_booklets(_pdf(n), [1] * n, bleed_mm=bleed)
    reader = PdfReader(io.BytesIO(out))
    sides = imposition_order(n)
    assert len(reader.pages) == len(sides)
    for page, (left, right) in zip(reader.pages, sides):
        half = float(page.mediabox.width) / 2
        xs = _text_xs(page)
        assert set(xs) == {f"P{left}", f"P{right}"}
        assert xs[f"P{left}"] < half < xs[f"P{right}"]
        # content of each page stays inside its own half (fold at the sheet centre)
        assert 0 < xs[f"P{left}"] < half < xs[f"P{right}"] < 2 * half


@pytest.mark.parametrize("booklet_size", [1, 2, 3])
def test_binding_margin_lands_on_the_fold_side(tmp_path, booklet_size):
    # inner (binding) margin 15 > outer 10: after imposition every placed page's content keeps
    # >= inner from the fold and >= outer from the sheet edge, left and right pages alike.
    # (Per-page margins are Grid.for_page / side_for_page; this checks they survive imposition.)
    cfg = Config(
        year=2025,
        planners=[],
        booklet_size=booklet_size,
        num_booklets=1,
        imposition=True,
        inner_margin=15,
        outer_margin=10,
    )
    out = export_agenda(cfg, tmp_path / "b.pdf").read_bytes()
    reader = PdfReader(io.BytesIO(out))
    inner, outer, eps = cfg.inner_margin, cfg.outer_margin, 0.1
    seen = {"left": 0, "right": 0}
    for page, pts in zip(reader.pages, drawn_points(out)):
        sheet_w = float(page.mediabox.width) * PT
        fold = sheet_w / 2
        for x, _ in pts:
            if min(abs(x), abs(x - fold), abs(x - sheet_w)) < 1e-3:
                continue  # page-boundary clip rectangles added by the merge, not content
            if x < fold:
                seen["left"] += 1
                assert outer - eps <= x <= fold - inner + eps, x
            else:
                seen["right"] += 1
                assert fold + inner - eps <= x <= sheet_w - outer + eps, x
    assert seen["left"] and seen["right"]


# ---------------------------------------------------------------- spreads and sheet size

def test_spread_sides():
    from agenda.imposition import spread_sides

    assert spread_sides(4) == [(None, 1), (2, 3), (4, None)]
    assert spread_sides(5) == [(None, 1), (2, 3), (4, 5)]
    assert spread_sides(0) == [(None, None)] or spread_sides(0) == []


_SMALL = {"year": 2026, "planners": ["weekly"], "daily_months": []}


def _sheet_mm(page):
    from agenda.imposition import MM_PT

    return float(page.mediabox.width) / MM_PT, float(page.mediabox.height) / MM_PT


def test_spreads_export_and_sheet_sizes(tmp_path):
    import math

    from pypdf import PdfReader

    from agenda.assembler import build_plan
    from agenda.exporter import export_agenda

    cfg = Config(**_SMALL, spreads=True, sheet_size="a4")
    n = len(build_plan(cfg))
    pages = PdfReader(str(export_agenda(cfg, tmp_path / "s.pdf"))).pages
    assert len(pages) == math.ceil((n + 1) / 2)
    w, h = _sheet_mm(pages[0])
    assert w > h and abs(w - 297) < 0.5 and abs(h - 210) < 0.5
    cfg = cfg.model_copy(update={"sheet_size": "letter"})
    w, h = _sheet_mm(PdfReader(str(export_agenda(cfg, tmp_path / "l.pdf"))).pages[0])
    assert abs(w - 279.4) < 0.5 and abs(h - 215.9) < 0.5


def test_imposition_sheet_size(tmp_path):
    from pypdf import PdfReader

    from agenda.exporter import export_agenda

    cfg = Config(year=2025, booklet_size=2, num_booklets=1, imposition=True, sheet_size="a4")
    w, h = _sheet_mm(PdfReader(str(export_agenda(cfg, tmp_path / "i.pdf"))).pages[0])
    assert abs(w - 297) < 0.5 and abs(h - 210) < 0.5


def test_spreads_rules():
    with pytest.raises(ValueError, match="imposition or spreads"):
        Config(imposition=True, spreads=True, booklet_folded=True)
    assert Config(spreads=True, crop_marks=True).crop_marks
    with pytest.raises(ValueError, match="crop_marks requires"):
        Config(crop_marks=True)


def test_cli_spreads_sheet_size(tmp_path):
    from pypdf import PdfReader

    from agenda.cli import main

    out = tmp_path / "c.pdf"
    code = main(["--year", "2026", "--planners", "weekly", "--daily-months", "",
                 "--spreads", "--sheet-size", "a4", "-o", str(out)])
    assert code == 0
    w, h = _sheet_mm(PdfReader(str(out)).pages[0])
    assert abs(w - 297) < 0.5
