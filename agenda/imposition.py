"""Page reordering for booklet printing (Qt-free, pure logic)."""

from __future__ import annotations


def imposition_order(n: int) -> list[tuple[int, int]]:
    """Print order of a folded (saddle-stitch) booklet of ``n`` pages.

    ``n`` must be a multiple of 4 (0 gives no sides). Returns the sheet sides in print order,
    each as a ``(left, right)`` pair of 1-based booklet page numbers: sheet ``s`` (1-based)
    has front ``(n-2s+2, 2s-1)`` then back ``(2s, n-2s+1)``. Every pair sums to ``n + 1``.
    """
    if n < 0 or n % 4:
        raise ValueError(f"booklet page count must be a non-negative multiple of 4, got {n}")
    sides: list[tuple[int, int]] = []
    for i in range(n // 4):
        sides.append((n - 2 * i, 2 * i + 1))  # front
        sides.append((2 * i + 2, n - 2 * i - 1))  # back
    return sides
