"""Page-number labels: pure logic (no drawing, no Qt)."""

from __future__ import annotations

from string import Formatter
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agenda.config import Config

Align = Literal["L", "C", "R"]
Side = Literal["left", "right"]


def validate_format(fmt: str) -> str:
    """Check a label format: 1-24 chars, only {n} and {total} fields, {n} required."""
    if not 1 <= len(fmt) <= 24:
        raise ValueError("page_number_format must be 1-24 characters")
    try:
        fields = [f for _, f, _, _ in Formatter().parse(fmt) if f is not None]
    except ValueError as exc:
        raise ValueError(f"invalid page_number_format: {exc}") from None
    if "n" not in fields:
        raise ValueError("page_number_format must contain {n}")
    if any(f not in ("n", "total") for f in fields):
        raise ValueError("page_number_format may only use the placeholders {n} and {total}")
    return fmt


def label_for(cfg: Config, page_number: int, total_pages: int) -> str | None:
    """Text printed on 1-based plan page ``page_number``, or None for no number."""
    if not cfg.page_numbers or page_number < cfg.page_number_first:
        return None
    offset = cfg.page_number_start - cfg.page_number_first
    return cfg.page_number_format.format(n=page_number + offset, total=total_pages + offset)


def align_for(side: Side, position: str) -> Align:
    """Text alignment inside the safe area; outer = away from the binding."""
    if position == "center":
        return "C"
    outer = "R" if side == "right" else "L"
    if position == "outer":
        return outer
    return "L" if outer == "R" else "R"


def x_for(side: Side, position: str, safe_x: float, safe_w: float, text_w: float) -> float:
    """Left x of the label text for the given position."""
    a = align_for(side, position)
    if a == "L":
        return safe_x
    if a == "R":
        return safe_x + safe_w - text_w
    return safe_x + (safe_w - text_w) / 2
