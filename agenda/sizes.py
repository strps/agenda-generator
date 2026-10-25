"""Named page sizes and custom WxH parsing, in mm."""

from __future__ import annotations

import re
from typing import NamedTuple

# Portrait (width, height) in mm.
SIZES: dict[str, tuple[float, float]] = {
    "half_letter": (139.7, 215.9),
    "a5": (148.0, 210.0),
    "b6": (125.0, 176.0),
    "letter": (215.9, 279.4),
    "a4": (210.0, 297.0),
}

MIN_MM = 50.0
MAX_MM = 1000.0

_CUSTOM_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)$")


class PageSize(NamedTuple):
    width: float  # mm
    height: float  # mm


def parse_size(spec: str) -> PageSize:
    """Parse a size name or custom ``WxH`` (mm) into a portrait-ordered-as-given size.

    Names are case-insensitive. Custom values keep the order given. Raises ValueError.
    """
    s = spec.strip()
    if s.lower() in SIZES:
        return PageSize(*SIZES[s.lower()])
    m = _CUSTOM_RE.match(s)
    if not m:
        raise ValueError(f"page_size must be one of {sorted(SIZES)} or 'WxH' in mm, got {spec!r}")
    w, h = float(m.group(1)), float(m.group(2))
    if not (MIN_MM <= w <= MAX_MM and MIN_MM <= h <= MAX_MM):
        raise ValueError(f"custom size must be {MIN_MM:g}-{MAX_MM:g} mm per side, got {w:g}x{h:g}")
    return PageSize(w, h)


def resolve_size(spec: str, orientation: str = "portrait") -> PageSize:
    """Final page (width, height) in mm. Portrait forces width <= height, landscape the reverse."""
    if orientation not in ("portrait", "landscape"):
        raise ValueError(f"orientation must be 'portrait' or 'landscape', got {orientation!r}")
    w, h = parse_size(spec)
    lo, hi = min(w, h), max(w, h)
    return PageSize(lo, hi) if orientation == "portrait" else PageSize(hi, lo)
