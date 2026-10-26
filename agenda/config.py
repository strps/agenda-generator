"""Parameter loading and validation (pydantic config model).

Single source of truth for all options (plan section 2 plus improvements.md amendments).
Size strings are kept raw here; ``agenda.sizes`` parses them.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)

from agenda.sizes import SIZES, PageSize, parse_size, resolve_size

QR_MAX_CHARS = 200
QR_MAX_COUNT = 24
FILLER_MODES = ("blank", "none")


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
    page_number_start: int = Field(1, ge=0, le=9999)  # number printed on the first numbered page
    page_number_first: int = Field(1, ge=1)  # 1-based plan page that gets the first number
    page_number_position: Literal["outer", "center", "inner"] = "outer"
    page_number_placement: Literal["margin", "footer"] = "margin"
    page_number_format: str = "{n}"  # placeholders {n} and {total}
    # Texts or URLs for the `qr` page: one QR code each (<= QR_MAX_COUNT entries of
    # <= QR_MAX_CHARS characters, the byte-mode capacity of a QR code with ~15% error correction).
    qr_urls: list[str] = Field(default_factory=list)
    # Per-template page settings (defaults = the former hard-coded page constants).
    daily_hour_start: int = Field(6, ge=0, le=23)
    daily_hour_end: int = Field(21, ge=0, le=23)
    # What fills the slot that keeps a week spread on a left page (see _check_filler): "blank",
    # "none" (no filler; the spread may start on a right page) or a 1-page catalog id. The
    # daily setting applies when the slot follows a day page, the weekly one otherwise.
    weekly_filler: str = "blank"
    daily_filler: str = "blank"
    # Per-month pages (BasePage.per_month) printed after each monthly overview / after each
    # month's last week; they are then left out of the optional/value-added block.
    month_start_pages: list[str] = Field(default_factory=list)
    month_end_pages: list[str] = Field(default_factory=list)
    schedule_first_hour: int = Field(7, ge=0, le=23)
    schedule_last_hour: int = Field(21, ge=0, le=23)
    habits_max: int = Field(20, ge=1, le=40)
    niche_entrepreneur_pages: int = Field(1, ge=1, le=20)
    niche_student_pages: int = Field(1, ge=1, le=20)
    niche_fitness_pages: int = Field(1, ge=1, le=20)
    # Back-matter page counts (0 removes them) and the minimum number of padding units.
    notes_pages: int = Field(1, ge=0, le=50)
    contacts_pages: int = Field(1, ge=0, le=50)
    extra_padding: int = Field(0, ge=0, le=200)
    # Day-page extras: holiday name, rotating phrase (built-in or from a file), dated extra data.
    daily_holidays: bool = True
    daily_quotes: bool = False
    daily_quotes_file: Path | None = None  # one phrase per line; None = built-in quotes
    daily_extra_file: Path | None = None  # dated lines shown on the matching day page

    # Calendar / locale
    year: int = Field(default_factory=lambda: _dt.date.today().year, ge=1900, le=2200)
    week_start: Literal["monday", "sunday"] = "monday"
    language: Literal["es", "en"] = "es"
    holiday_country: str = "CR"
    holidays_file: Path | None = None  # user holidays (MM-DD text), merged with the library

    # Look & output
    theme: str = "minimal"
    # Per-color overrides on top of the theme palette (None = use the theme's color).
    color_ink: str | None = None
    color_muted: str | None = None
    color_line: str | None = None
    color_accent: str | None = None
    color_tint: str | None = None
    color_weekend_fill: str | None = None
    color_holiday_fill: str | None = None
    font_primary: str = "inter"  # headings, titles, bold text: "inter" or a .ttf/.otf path
    font_secondary: str = "inter"  # body text, labels, numbers
    imposition: bool = False
    crop_marks: bool = False
    spreads: bool = False
    sheet_size: Literal["auto", "letter", "a4"] = "auto"
    output: Path = Path("agenda.pdf")
    debug_grid: bool = False

    @field_validator("page_size")
    @classmethod
    def _check_page_size(cls, v: str) -> str:
        v = v.strip()
        parse_size(v)  # raises ValueError on bad names / out-of-range custom sizes
        return v.lower() if v.lower() in SIZES else v

    @field_validator(
        "color_ink",
        "color_muted",
        "color_line",
        "color_accent",
        "color_tint",
        "color_weekend_fill",
        "color_holiday_fill",
    )
    @classmethod
    def _check_color(cls, v: str | None, info: ValidationInfo) -> str | None:
        if v is None:
            return None
        from agenda.themes import normalize_hex

        try:
            return normalize_hex(v)
        except ValueError:
            raise ValueError(f"{info.field_name} must be a hex color like #c85028") from None

    @field_validator("font_primary", "font_secondary")
    @classmethod
    def _check_font(cls, v: str, info: ValidationInfo) -> str:
        from agenda.fonts import BUILTIN, resolve

        v = v.strip()
        if v.lower() in BUILTIN:
            return v.lower()
        try:
            resolve(v)
        except ValueError as e:
            raise ValueError(f"{info.field_name}: {e}") from None
        return v

    @field_validator("page_number_format")
    @classmethod
    def _check_number_format(cls, v: str) -> str:
        from agenda.numbering import validate_format

        return validate_format(v)

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

    @field_validator("weekly_filler", "daily_filler")
    @classmethod
    def _check_filler(cls, v: str, info: ValidationInfo) -> str:
        """``blank``, ``none`` or a single-page catalog id with no side constraint."""
        from agenda.catalog import get_page

        v = v.strip().lower()
        if v in FILLER_MODES:
            return v
        try:
            page = get_page(v)
        except KeyError:
            raise ValueError(
                f"{info.field_name} must be blank, none or a page id; unknown page {v!r}"
            ) from None
        if page.pages != 1 or page.starts_on != "any":
            raise ValueError(f"{info.field_name}: page {v!r} must be a single page with no side")
        return v

    @field_validator("month_start_pages", "month_end_pages")
    @classmethod
    def _check_month_pages(cls, v: list[str], info: ValidationInfo) -> list[str]:
        """Ids of per-month catalog pages, each once."""
        from agenda.catalog import get_page

        out = [i.strip() for i in v]
        for i in out:
            try:
                page = get_page(i)
            except KeyError:
                raise ValueError(f"{info.field_name}: unknown page {i!r}") from None
            if not page.per_month:
                raise ValueError(f"{info.field_name}: page {i!r} is not a per-month page")
        if len(set(out)) != len(out):
            raise ValueError(f"{info.field_name}: a page is listed twice")
        return out

    @field_validator("holiday_country")
    @classmethod
    def _upper_country(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("daily_quotes_file", "daily_extra_file", "holidays_file")
    @classmethod
    def _check_data_file(cls, v: Path | None, info: ValidationInfo) -> Path | None:
        """A set file must exist and parse. Lazy import keeps day_extras Config-free."""
        if v is None:
            return v
        from agenda.day_extras import parse_dated, read_lines

        lines = read_lines(v)
        if info.field_name != "daily_quotes_file":
            parse_dated(lines, 2000)
        return v

    @model_validator(mode="after")
    def _resolve_preset(self) -> Config:
        """Single resolution point: an unset/empty ``pages`` is filled from ``preset``."""
        if self.preset and not self.pages:
            from agenda.catalog import preset_pages  # lazy: the catalog imports this module

            self.__dict__["pages"] = preset_pages(self.preset)  # no re-validation (no recursion)
        return self

    @model_validator(mode="after")
    def _check_month_placement(self) -> Config:
        both = set(self.month_start_pages) & set(self.month_end_pages)
        if both:
            raise ValueError(
                f"{', '.join(sorted(both))}: a page can be at the start or the end of each "
                "month, not both"
            )
        return self

    @model_validator(mode="after")
    def _check_booklet_rules(self) -> Config:
        if self.imposition and not self.booklet_folded:
            raise ValueError("imposition requires booklet_folded=true")
        if self.daily_hour_start >= self.daily_hour_end:
            raise ValueError("daily_hour_start must be less than daily_hour_end")
        if self.schedule_first_hour >= self.schedule_last_hour:
            raise ValueError("schedule_first_hour must be less than schedule_last_hour")
        if self.imposition and self.spreads:
            raise ValueError("choose either imposition or spreads, not both")
        if self.crop_marks and not (self.imposition or self.spreads):
            raise ValueError("crop_marks requires imposition=true or spreads=true")
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
