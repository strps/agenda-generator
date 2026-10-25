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
