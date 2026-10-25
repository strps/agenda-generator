"""Parameter loading and validation (pydantic config model).

Single source of truth for all options (plan section 2 plus improvements.md amendments).
Size strings are kept raw here; ``agenda.sizes`` parses them.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agenda.sizes import SIZES, PageSize, parse_size, resolve_size

QR_MAX_CHARS = 200
QR_MAX_COUNT = 24


def _parse_months(value: object) -> object:
    """Accept ``"1-12"``, ``"1,3,5-6"`` or a list of ints."""
    if not isinstance(value, str):
        return value
    months: list[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        lo, sep, hi = part.partition("-")
        try:
            a, b = int(lo), int(hi) if sep else int(lo)
        except ValueError as exc:
            raise ValueError(f"invalid month spec: {part!r}") from exc
        if a > b:
            raise ValueError(f"invalid month range: {part!r}")
        months.extend(range(a, b + 1))
    return months


class Config(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    # Page geometry. ``page_size`` is a raw string: a name or custom "WxH" in mm
    # (parsed by agenda.sizes).
    page_size: str = "half_letter"
    orientation: Literal["portrait", "landscape"] = "portrait"
    inner_margin: float = Field(15.0, ge=0)  # mm, binding side
    outer_margin: float = Field(10.0, ge=0)  # mm
    bleed: float = Field(3.0, ge=0)  # mm, gap before each crop mark (needs crop_marks)

    # Booklets
    booklet_size: int = Field(5, ge=1)
    booklet_unit: Literal["sheets", "pages"] = "sheets"
    booklet_folded: bool = True
    num_booklets: int | Literal["auto"] = "auto"
    pad_with: str = "notes"  # catalog page id used to fill the last booklet (see _check_pad_with)
    separate_covers: bool = False
    creep_mm: float = Field(0.0, ge=0)

    # Content
    planners: list[Literal["weekly", "daily"]] = Field(default_factory=lambda: ["weekly", "daily"])
    daily_months: list[int] = Field(default_factory=lambda: list(range(1, 13)))
    pages: list[str] | None = None  # catalog IDs; None = all core pages (resolved by catalog)
    # Selects ``pages`` by value score (agenda.catalog.preset_pages). Only used when ``pages`` is
    # empty: explicit ``pages`` always win over the preset.
    preset: Literal["essential", "complete", "premium"] | None = None
    notes_pattern: Literal["lined", "dotted", "grid", "blank"] = "dotted"
    page_numbers: bool = False
    # Texts or URLs for the `qr` page: one QR code each (<= QR_MAX_COUNT entries of
    # <= QR_MAX_CHARS characters, the byte-mode capacity of a QR code with ~15% error correction).
    qr_urls: list[str] = Field(default_factory=list)

    # Calendar / locale
    year: int = Field(default_factory=lambda: _dt.date.today().year, ge=1900, le=2200)
    week_start: Literal["monday", "sunday"] = "monday"
    language: Literal["es", "en"] = "es"
    holiday_country: str = "CR"

    # Look & output
    theme: str = "minimal"
    imposition: bool = False
    crop_marks: bool = False
    output: Path = Path("agenda.pdf")
    debug_grid: bool = False

    @field_validator("page_size")
    @classmethod
    def _check_page_size(cls, v: str) -> str:
        v = v.strip()
        parse_size(v)  # raises ValueError on bad names / out-of-range custom sizes
        return v.lower() if v.lower() in SIZES else v

    @field_validator("daily_months", mode="before")
    @classmethod
    def _months(cls, v: object) -> object:
        return _parse_months(v)

    @field_validator("daily_months")
    @classmethod
    def _check_months(cls, v: list[int]) -> list[int]:
        if any(not 1 <= m <= 12 for m in v):
            raise ValueError("daily_months values must be 1-12")
        return sorted(set(v))

    @field_validator("planners")
    @classmethod
    def _dedupe_planners(cls, v: list[str]) -> list[str]:
        return list(dict.fromkeys(v))

    @field_validator("qr_urls")
    @classmethod
    def _check_qr_urls(cls, v: list[str]) -> list[str]:
        v = [u.strip() for u in v]
        if any(not u for u in v):
            raise ValueError("qr_urls entries must not be empty")
        if any(len(u) > QR_MAX_CHARS for u in v):
            raise ValueError(f"qr_urls entries must be at most {QR_MAX_CHARS} characters")
        if len(v) > QR_MAX_COUNT:
            raise ValueError(f"qr_urls accepts at most {QR_MAX_COUNT} entries")
        return v

    @field_validator("num_booklets")
    @classmethod
    def _check_num_booklets(cls, v: int | str) -> int | str:
        if isinstance(v, int) and v < 1:
            raise ValueError("num_booklets must be >= 1 or 'auto'")
        return v

    @field_validator("pad_with")
    @classmethod
    def _check_pad_with(cls, v: str) -> str:
        """Must be a catalog page id. Lazy import: the catalog imports this module."""
        from agenda.catalog import get_page

        v = v.strip()
        try:
            get_page(v)
        except KeyError as exc:
            raise ValueError(exc.args[0]) from None
        return v

    @field_validator("holiday_country")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.strip().upper()

    @model_validator(mode="after")
    def _resolve_preset(self) -> Config:
        """Single resolution point: an unset/empty ``pages`` is filled from ``preset``."""
        if self.preset and not self.pages:
            from agenda.catalog import preset_pages  # lazy: the catalog imports this module

            self.__dict__["pages"] = preset_pages(self.preset)  # no re-validation (no recursion)
        return self

    @model_validator(mode="after")
    def _check_booklet_rules(self) -> Config:
        if self.imposition and not self.booklet_folded:
            raise ValueError("imposition requires booklet_folded=true")
        if self.crop_marks and not self.imposition:
            raise ValueError("crop_marks requires imposition=true")
        if self.booklet_unit == "pages":
            # folded: 4 pages per sheet; flat: 2 pages per sheet (double-sided)
            step = 4 if self.booklet_folded else 2
            if self.booklet_size % step:
                kind = "folded" if self.booklet_folded else "flat"
                raise ValueError(
                    f"{kind} booklets need a page count that is a multiple of {step} "
                    f"(got booklet_size={self.booklet_size} pages)"
                )
        return self

    @property
    def page_dimensions(self) -> PageSize:
        """Final page (width, height) in mm after orientation."""
        return resolve_size(self.page_size, self.orientation)

    @property
    def pages_per_booklet(self) -> int:
        """Pages in one booklet (4 per folded sheet, 2 per flat sheet)."""
        if self.booklet_unit == "pages":
            return self.booklet_size
        return self.booklet_size * (4 if self.booklet_folded else 2)
