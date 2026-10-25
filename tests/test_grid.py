import pytest

from agenda import tokens
from agenda.config import Config
from agenda.grid import Grid

SIZES = ["half_letter", "a5"]


def make(size, side="right"):
    return Grid.from_config(Config(page_size=size), side=side)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("side", ["left", "right"])
def test_columns_sum_with_gutters(size, side):
    g = make(size, side)
    assert g.columns == 6
    x, w = g.col(0, 6)
    assert x == pytest.approx(g.safe.x)
    assert w == pytest.approx(g.safe.w)
    assert 6 * g.col_width + 5 * g.gutter == pytest.approx(g.safe.w)
    assert g.col_x(5) + g.col_width == pytest.approx(g.safe.x2)
    assert g.col(0, 2)[1] + g.gutter + g.col(2, 2)[1] + g.gutter + g.col(4, 2)[1] == pytest.approx(
        g.safe.w
    )


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("side", ["left", "right"])
def test_everything_inside_page(size, side):
    g = make(size, side)
    for r in (g.safe, g.header, g.footer, g.content, g.span(0, 6), g.span(5, 1)):
        assert r.x >= 0 and r.y >= 0 and r.x2 <= g.page_w + 1e-9 and r.y2 <= g.page_h + 1e-9
    assert g.header.y2 <= g.content.y
    assert g.content.y2 <= g.footer.y + 1e-9


def test_margins_by_side():
    r, l_ = make("a5", "right"), make("a5", "left")
    assert (r.left, r.right) == (15, 10)
    assert (l_.left, l_.right) == (10, 15)
    assert r.for_side("left").left == 10


@pytest.mark.parametrize("size", SIZES)
def test_baseline_spacing(size):
    g = make(size)
    assert g.baseline == tokens.BASELINE == 5.0
    assert g.rows > 0
    assert g.content.h == pytest.approx(g.rows * 5)
    assert all(g.row(n + 1) - g.row(n) == pytest.approx(5) for n in range(g.rows))
    assert g.row(g.rows) == pytest.approx(g.content.y2)
    assert g.snap(g.row(3) + 1.2) == pytest.approx(g.row(3))
    assert g.snap(g.row(3) + 3.0) == pytest.approx(g.row(4))


def test_span_and_errors():
    g = make("half_letter")
    r = g.span(col=2, cols=2, row=1, rows=4)
    assert r.x == pytest.approx(g.col_x(2)) and r.h == 20 and r.y == g.row(1)
    with pytest.raises(ValueError):
        g.col(5, 2)
    with pytest.raises(ValueError):
        g.span(rows=g.rows + 1)
    with pytest.raises(ValueError):
        Grid(100, 100, 15, 10, side="middle")
    with pytest.raises(ValueError):
        Grid(60, 60, 30, 30)
