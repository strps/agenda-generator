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
    page_size: str = Field(
        "half_letter",
        description="Page size: a name or custom WxH in mm.",
        json_schema_extra={
            "detail": (
                "Size of the finished page. Use a known name (half_letter, "
                "a5, letter, a4, b6) or a custom size written as WxH in "
                "millimetres. Orientation is applied on top of it."
            ),
            "cli": {"flags": ["--page-size", "--size"], "type": "str"},
        },
    )
    orientation: Literal["portrait", "landscape"] = Field(
        "portrait",
        description="Page orientation.",
        json_schema_extra={
            "detail": (
                "Whether the page is taller than wide (portrait) or wider "
                "than tall (landscape). It swaps the width and height of the "
                "page size for every page."
            ),
            "cli": {"type": "str"},
        },
    )
    inner_margin: float = Field(
        15.0,
        ge=0,
        description="Margin on the binding side, in mm.",
        json_schema_extra={
            "detail": (
                "Free space, in mm, on the side of the page where the booklet "
                "is bound. A larger value moves the content away from the "
                "fold and shrinks the content width."
            ),
            "cli": {},
        },
    )  # mm, binding side
    outer_margin: float = Field(
        10.0,
        ge=0,
        description="Margin on the outer edges, in mm.",
        json_schema_extra={
            "detail": (
                "Free space, in mm, on the outer edges of the page, away from "
                "the binding. A larger value shrinks the area available for "
                "the content."
            ),
            "cli": {},
        },
    )  # mm
    bleed: float = Field(
        3.0,
        ge=0,
        description="Gap before each crop mark, in mm.",
        json_schema_extra={
            "detail": (
                "Gap, in mm, left between the page and each crop mark. It "
                "only has an effect when crop_marks is on, which in turn "
                "needs imposition or spreads."
            ),
            "cli": {},
        },
    )  # mm, gap before each crop mark (needs crop_marks)

    # Booklets
    booklet_size: int = Field(
        5,
        ge=1,
        description="Size of one booklet, in sheets or pages.",
        json_schema_extra={
            "detail": (
                "How big one booklet is. It is counted in sheets or in pages "
                "depending on booklet_unit (sheets or pages). With pages it "
                "must be a multiple of 4 for folded booklets and of 2 for "
                "flat ones."
            ),
            "cli": {"flags": ["--booklet-size", "--booklet"]},
        },
    )
    booklet_unit: Literal["sheets", "pages"] = Field(
        "sheets",
        description="Unit of the booklet size.",
        json_schema_extra={
            "detail": (
                "Whether booklet_size counts sheets or pages. A folded sheet "
                "holds 4 pages and a flat double-sided sheet holds 2, so 5 "
                "sheets are 20 folded pages."
            ),
            "cli": {"flags": ["--booklet-unit", "--unit"], "type": "str"},
        },
    )
    booklet_folded: bool = Field(
        True,
        description="Folded (4 pages per sheet) or flat booklets.",
        json_schema_extra={
            "detail": (
                "On: saddle-stitched booklets with 4 pages per sheet. Off: "
                "flat double-sided sheets with 2 pages per sheet. Imposition "
                "requires folded booklets."
            ),
            "cli": {"flags": ["--folded/--flat"]},
        },
    )
    num_booklets: int | Literal["auto"] = Field(
        "auto",
        description="Number of booklets, or auto.",
        json_schema_extra={
            "detail": (
                "How many booklets the agenda is split into. Use auto to "
                "derive the number from the content, or a whole number of at "
                "least 1. The last booklet is filled with pad_with."
            ),
            "cli": {"type": "str"},
        },
    )
    pad_with: str = Field(
        "notes",
        description="Page used to fill the last booklet.",
        json_schema_extra={
            "detail": (
                "Catalog page repeated to fill the last booklet so that it "
                "ends on a whole sheet. These filler pages show as padding in "
                "the section bar. The default is notes. The page is set up in "
                "its own section (e.g. the Notes pattern), which is badged "
                "padding."
            ),
            "cli": {"type": "str"},
        },
    )  # catalog page id used to fill the last booklet (see _check_pad_with)
    separate_covers: bool = Field(
        False,
        description="Keep the covers apart from the booklets.",
        json_schema_extra={
            "detail": (
                "When on, the cover and back cover are excluded from the "
                "booklet count, so padding goes before the back cover and the "
                "covers can be printed separately on card stock."
            ),
            "cli": {},
        },
    )
    creep_mm: float = Field(
        0.0,
        ge=0,
        description="Creep compensation for folded sheets, in mm.",
        json_schema_extra={
            "detail": (
                "Shift, in mm, applied to the inner pages of folded sheets on "
                "the imposed output to compensate for paper thickness. It is "
                "negligible for small booklets and 0 disables it."
            ),
            "cli": {},
        },
    )

    # Content
    planners: list[Literal["weekly", "daily"]] = Field(
        default_factory=lambda: ["weekly", "daily"],
        description="Which planner pages to include.",
        json_schema_extra={
            "detail": (
                "Which planner page types are generated: weekly, daily or "
                "both. Daily pages are limited to the months in daily_months, "
                "which also limits the page count."
            ),
            "cli": {"type": "str", "csv": True},
        },
    )
    daily_months: list[int] = Field(
        default_factory=lambda: list(range(1, 13)),
        description="Months that get daily pages.",
        json_schema_extra={
            "detail": (
                "Months (1-12) that get daily pages, for example 1-6,9. Fewer "
                "months give fewer pages and a thinner agenda. It only "
                "matters when the daily planner is selected."
            ),
            "cli": {"type": "str"},
        },
    )
    pages: list[str] | None = Field(
        None,
        description="Catalog pages to include.",
        json_schema_extra={
            "detail": (
                "Explicit list of catalog page ids to include. When set, it "
                "always overrides the preset. When empty and no preset is "
                "chosen, all core pages are used."
            ),
            "cli": {"type": "str", "csv": True, "skip": True},
        },
    )  # catalog IDs; None = all core pages (resolved by catalog)
    # Selects ``pages`` by value score (agenda.catalog.preset_pages). Only used when ``pages`` is
    # empty: explicit ``pages`` always win over the preset.
    preset: Literal["essential", "complete", "premium"] | None = Field(
        None,
        description="Page selection by value score.",
        json_schema_extra={
            "detail": (
                "Selects pages by value score: essential, complete or "
                "premium. It is only used when pages is empty, because "
                "explicit pages always win over the preset."
            ),
            "cli": {"type": "str"},
        },
    )
    notes_pattern: Literal["lined", "dotted", "grid", "blank"] = Field(
        "dotted",
        description="Pattern of the notes pages.",
        json_schema_extra={
            "detail": (
                "Ruling printed on the notes pages: lined, dotted, grid or "
                "blank. It also applies to notes pages added as booklet "
                "padding."
            ),
            "cli": {"type": "str"},
        },
    )
    page_numbers: bool = Field(
        False,
        description="Print page numbers on the pages.",
        json_schema_extra={
            "detail": (
                "When on, a page number is printed on each page. When off, "
                "the pages carry no numbers. Start, first page, position, "
                "placement and format refine it (page_number_start, "
                "page_number_first, page_number_position, "
                "page_number_placement, page_number_format)."
            ),
            "cli": {},
        },
    )
    page_number_start: int = Field(
        1,
        ge=0,
        le=9999,
        description="Number printed on the first numbered page.",
        json_schema_extra={
            "detail": (
                "Number printed on the first numbered page (0-9999, default "
                "1). Only used when page_numbers is on."
            ),
            "cli": {},
        },
    )  # number printed on the first numbered page
    page_number_first: int = Field(
        1,
        ge=1,
        description="Plan page that gets the first number.",
        json_schema_extra={
            "detail": (
                "1-based plan page that gets the first number (default 1). "
                "Earlier pages are unnumbered, e.g. 3 skips the cover and "
                "inside cover. Only used when page_numbers is on."
            ),
            "cli": {},
        },
    )  # 1-based plan page that gets the first number
    page_number_position: Literal["outer", "center", "inner"] = Field(
        "outer",
        description="Where the number sits: outer, center or inner.",
        json_schema_extra={
            "detail": (
                "Horizontal position: outer (away from the binding, default), "
                "center or inner (next to the binding). Only used when "
                "page_numbers is on."
            ),
            "cli": {"type": "str"},
        },
    )
    page_number_placement: Literal["margin", "footer"] = Field(
        "margin",
        description="Number in the bottom margin or in the page footer.",
        json_schema_extra={
            "detail": (
                "margin (default) prints the number in the bottom margin "
                "below the page content; footer prints it inside the page "
                "footer band. Only used when page_numbers is on."
            ),
            "cli": {"type": "str"},
        },
    )
    page_number_format: str = Field(
        "{n}",
        description="Label text; {n} is the number, {total} the last one.",
        json_schema_extra={
            "detail": (
                "Label text, 1-24 characters. {n} is the page number "
                "(required) and {total} the last number, e.g. '{n} / "
                "{total}'. Only used when page_numbers is on."
            ),
            "cli": {"type": "str"},
        },
    )  # placeholders {n} and {total}
    # Texts or URLs for the `qr` page: one QR code each (<= QR_MAX_COUNT entries of
    # <= QR_MAX_CHARS characters, the byte-mode capacity of a QR code with ~15% error correction).
    qr_urls: list[str] = Field(
        default_factory=list,
        description="Texts or URLs for the QR page, one per line.",
        json_schema_extra={
            "detail": (
                "Texts or URLs for the qr page, one QR code each, entered one "
                "per line. At most 24 entries of at most 200 characters, and "
                "empty lines are not allowed."
            ),
            "cli": {"skip": True},
        },
    )
    # Per-template page settings (defaults = the former hard-coded page constants).
    daily_hour_start: int = Field(
        6,
        ge=0,
        le=23,
        description="First hour printed on day pages (0-23).",
        json_schema_extra={
            "detail": (
                "First hour of the hourly schedule on day pages, 0-23 "
                "(default 6, shown as 06:00). It must be less than "
                "daily_hour_end. The page still shows fewer hours when they "
                "do not fit."
            ),
            "cli": {},
        },
    )
    daily_hour_end: int = Field(
        21,
        ge=0,
        le=23,
        description="Last hour printed on day pages (0-23).",
        json_schema_extra={
            "detail": (
                "Last hour of the hourly schedule on day pages, 0-23 (default "
                "21, shown as 21:00). It must be greater than "
                "daily_hour_start. The page still shows fewer hours when they "
                "do not fit."
            ),
            "cli": {},
        },
    )
    # What fills the slot that keeps a week spread on a left page (see _check_filler): "blank",
    # "none" (no filler; the spread may start on a right page) or a 1-page catalog id. The
    # daily setting applies when the slot follows a day page, the weekly one otherwise.
    weekly_filler: str = Field(
        "blank",
        description=("What fills the page before a week spread: blank, none or a page."),
        json_schema_extra={
            "detail": (
                "Week spreads start on a left page, so a filler page is added "
                "before a spread that would start on a right page. blank (the "
                "default) leaves it empty; none adds no filler, so such a "
                "spread starts on a right page and is split across two "
                "leaves; a single-page catalog id (e.g. notes or todo) prints "
                "that page in the slot. Used when the slot does not follow a "
                "day page."
            ),
            "cli": {"type": "str"},
        },
    )
    daily_filler: str = Field(
        "blank",
        description=("What fills the page after a week's day pages: blank, none or a page."),
        json_schema_extra={
            "detail": (
                "Same as weekly_filler, for the filler slot that follows the "
                "last day page of a week (before the next week spread). blank "
                "(the default), none or a single-page catalog id such as "
                "notes. With both planners on, most fillers are in this slot."
            ),
            "cli": {"type": "str"},
        },
    )
    # Per-month pages (BasePage.per_month) printed after each monthly overview / after each
    # month's last week; they are then left out of the optional/value-added block.
    month_start_pages: list[str] = Field(
        default_factory=list,
        description="Per-month pages printed right after each monthly page.",
        json_schema_extra={
            "detail": (
                "Per-month pages (budget, habits, monthly_review, health, "
                "quotes) printed right after each monthly page, with that "
                "month's date. A page listed here is not printed again after "
                "the planner, and cannot also be in month_end_pages."
            ),
            "cli": {"type": "str", "csv": True},
        },
    )
    month_end_pages: list[str] = Field(
        default_factory=list,
        description="Per-month pages printed after each month's last week.",
        json_schema_extra={
            "detail": (
                "Per-month pages printed after the last week of each month, "
                "with that month's date. A week belongs to the month it "
                "starts in, so the page can follow a day or two of the next "
                "month. A page listed here is not printed again after the "
                "planner."
            ),
            "cli": {"type": "str", "csv": True},
        },
    )
    schedule_first_hour: int = Field(
        7,
        ge=0,
        le=23,
        description="First hour of the weekly schedule (0-23).",
        json_schema_extra={
            "detail": (
                "Hour of the first row of the weekly schedule page, 0-23 "
                "(default 7). It must be less than schedule_last_hour. The "
                "page still shows fewer rows when they do not fit."
            ),
            "cli": {},
        },
    )
    schedule_last_hour: int = Field(
        21,
        ge=0,
        le=23,
        description="Last hour of the weekly schedule (0-23).",
        json_schema_extra={
            "detail": (
                "Hour of the last row of the weekly schedule page, 0-23 "
                "(default 21), which caps the number of hours. It must be "
                "greater than schedule_first_hour. The page still shows fewer "
                "rows when they do not fit."
            ),
            "cli": {},
        },
    )
    habits_max: int = Field(
        20,
        ge=1,
        le=40,
        description="Maximum habit rows per month (1-40).",
        json_schema_extra={
            "detail": (
                "Maximum number of habit rows on each monthly habit tracker "
                "page, 1-40 (default 20). The page still shows fewer rows "
                "when they do not fit."
            ),
            "cli": {},
        },
    )
    niche_entrepreneur_pages: int = Field(
        1,
        ge=1,
        le=20,
        description="Number of Entrepreneur pack pages (1-20).",
        json_schema_extra={
            "detail": (
                "How many copies of the Entrepreneur pack page are printed, "
                "1-20 (default 1). It only applies when niche_entrepreneur is "
                "in pages."
            ),
            "cli": {},
        },
    )
    niche_student_pages: int = Field(
        1,
        ge=1,
        le=20,
        description="Number of Student pack pages (1-20).",
        json_schema_extra={
            "detail": (
                "How many copies of the Student pack page are printed, 1-20 "
                "(default 1). It only applies when niche_student is in pages."
            ),
            "cli": {},
        },
    )
    niche_fitness_pages: int = Field(
        1,
        ge=1,
        le=20,
        description="Number of Fitness pack pages (1-20).",
        json_schema_extra={
            "detail": (
                "How many copies of the Fitness pack page are printed, 1-20 "
                "(default 1). It only applies when niche_fitness is in pages."
            ),
            "cli": {},
        },
    )
    # Back-matter page counts (0 removes them) and the minimum number of padding units.
    notes_pages: int = Field(
        1,
        ge=0,
        le=50,
        description="Number of back-matter Notes pages (0-50).",
        json_schema_extra={
            "detail": (
                "How many Notes pages are printed in the back matter, 0-50 "
                "(default 1). 0 removes them. Padding made with "
                "pad_with=notes is separate and is set by extra_padding."
            ),
            "cli": {},
        },
    )
    contacts_pages: int = Field(
        1,
        ge=0,
        le=50,
        description="Number of back-matter Contacts pages (0-50).",
        json_schema_extra={
            "detail": (
                "How many Contacts pages are printed in the back matter, 0-50 "
                "(default 1). 0 removes them and the Contacts section is then "
                "off."
            ),
            "cli": {},
        },
    )
    extra_padding: int = Field(
        0,
        ge=0,
        le=200,
        description="Minimum number of padding pages to add (0-200).",
        json_schema_extra={
            "detail": (
                "Minimum number of padding units (copies of the pad_with "
                "page, or blank pages) put before the back cover, 0-200 "
                "(default 0). The agenda may get more padding than asked, to "
                "complete the last booklet, so booklets stay whole."
            ),
            "cli": {},
        },
    )
    # Day-page extras: holiday name, rotating phrase (built-in or from a file), dated extra data.
    daily_holidays: bool = Field(
        True,
        description="Print the holiday name on day pages.",
        json_schema_extra={
            "detail": (
                "When on (the default), the day pages print the name of the "
                "day's holiday in the header, before the week number. It uses "
                "the same holidays as the calendar pages, including those "
                "from holidays_file."
            ),
            "cli": {},
        },
    )
    daily_quotes: bool = Field(
        False,
        description="Print a rotating phrase on day pages.",
        json_schema_extra={
            "detail": (
                "When on, the footer of each day page shows an inspirational "
                "phrase. Phrases rotate: one per day of the year, cycling "
                "through the list. Off by default."
            ),
            "cli": {},
        },
    )
    daily_quotes_file: Path | None = Field(
        None,
        description="CSV file with one phrase per row.",
        json_schema_extra={
            "detail": (
                "Optional CSV file (any spreadsheet can make it) with one "
                "phrase per row in the first column; a header row such as "
                "'phrase' is optional. The phrases rotate, one per day of the "
                "year, cycling. Empty means the built-in phrases of the "
                "chosen language. Used only with daily_quotes."
            ),
            "cli": {},
        },
    )  # one phrase per row; None = built-in quotes
    daily_extra_file: Path | None = Field(
        None,
        description="CSV file of dated notes shown on day pages.",
        json_schema_extra={
            "detail": (
                "Optional CSV file (any spreadsheet can make it) with the "
                "columns month, day, text and an optional year (empty = "
                "every year); a header row is optional. The text is shown in "
                "the footer of the matching day page. Several entries on one "
                "date are joined."
            ),
            "cli": {},
        },
    )  # dated rows shown on the matching day page

    # Calendar / locale
    year: int = Field(
        default_factory=lambda: _dt.date.today().year,
        ge=1900,
        le=2200,
        description="Calendar year of the agenda.",
        json_schema_extra={
            "detail": (
                "Year of the calendar (1900-2200). It sets all dates, "
                "weekdays and holidays on the monthly, weekly and daily "
                "pages."
            ),
            "cli": {},
        },
    )
    week_start: Literal["monday", "sunday"] = Field(
        "monday",
        description="First day of the week.",
        json_schema_extra={
            "detail": (
                "First day of the week, monday or sunday. It changes the "
                "column order of the monthly grids and where each weekly page "
                "begins."
            ),
            "cli": {"type": "str"},
        },
    )
    language: Literal["es", "en"] = Field(
        "es",
        description="Language of the printed texts.",
        json_schema_extra={
            "detail": (
                "Language of month names, weekdays and other printed texts: "
                "es (Spanish) or en (English)."
            ),
            "cli": {"type": "str"},
        },
    )
    holiday_country: str = Field(
        "CR",
        description="Country code used for holidays, e.g. CR.",
        json_schema_extra={
            "detail": (
                "ISO country code, for example CR, whose public holidays are "
                "marked on the calendar pages. It is converted to upper case."
            ),
            "cli": {"type": "str"},
        },
    )
    holidays_file: Path | None = Field(
        None,
        description="Extra holidays CSV file, merged with the library.",
        json_schema_extra={
            "detail": (
                "Optional CSV file (any spreadsheet can make it) of your own "
                "holidays, with the columns month, day, name and an optional "
                "year (empty = every year); a header row is optional. They "
                "are merged with the country holidays and shown the same way "
                "on every page."
            ),
            "cli": {},
        },
    )  # user holidays (CSV rows), merged with the library

    # Look & output
    theme: str = Field(
        "minimal",
        description="Color palette of the PDF.",
        json_schema_extra={
            "detail": (
                "Name of the color palette of the PDF: minimal (default), "
                "mono, ocean, forest, blush, lavender or peony. An unknown name "
                "renders as minimal "
                "(the command line warns)."
            ),
            "cli": {"type": "str"},
        },
    )
    # Per-color overrides on top of the theme palette (None = use the theme's color).
    color_ink: str | None = Field(
        None,
        description="Main text color of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Main text color of the PDF, used for titles, day numbers and "
                "body text. Hex color such as #c85028 (also #abc or without "
                "the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_muted: str | None = Field(
        None,
        description="Secondary text color of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Secondary text color of the PDF, used for labels, captions, "
                "week numbers and page numbers. Hex color such as #c85028 "
                "(also #abc or without the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_line: str | None = Field(
        None,
        description="Line color of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Line color of the PDF, used for rules, grid lines and dots. "
                "Hex color such as #c85028 (also #abc or without the #). "
                "Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_accent: str | None = Field(
        None,
        description="Accent color of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Accent color of the PDF, used for month titles, holiday "
                "marks and highlights. Hex color such as #c85028 (also #abc "
                "or without the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_tint: str | None = Field(
        None,
        description="Light tint color of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Light tint color of the PDF, used for header bands and soft "
                "backgrounds. Hex color such as #c85028 (also #abc or without "
                "the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_weekend_fill: str | None = Field(
        None,
        description="Weekend cell fill of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Weekend cell fill of the PDF, used for the background of "
                "weekend days in calendars. Hex color such as #c85028 (also "
                "#abc or without the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    color_holiday_fill: str | None = Field(
        None,
        description="Holiday cell fill of the PDF (empty = theme).",
        json_schema_extra={
            "detail": (
                "Holiday cell fill of the PDF, used for the background of "
                "holiday days in calendars. Hex color such as #c85028 (also "
                "#abc or without the #). Empty = use the theme's color."
            ),
            "cli": {"type": "str"},
        },
    )
    font_primary: str = Field(
        "inter",
        description="Font of headings, titles and bold text.",
        json_schema_extra={
            "detail": (
                "Font for headings, titles and every bold text: the bundled "
                '"inter" or the path of a .ttf/.otf file. Bold/italic '
                "variants are looked up next to the file (MyFont-Regular.ttf "
                "-> MyFont-Bold.ttf); missing styles use the regular file. "
                "The font must contain the characters of the agenda language."
            ),
            "cli": {"type": "str"},
        },
    )  # headings, titles, bold text: "inter" or a .ttf/.otf path
    font_secondary: str = Field(
        "inter",
        description="Font of body text, labels and numbers.",
        json_schema_extra={
            "detail": (
                "Font for body text, labels, numbers and italic text: the "
                'bundled "inter" or the path of a .ttf/.otf file. Bold/italic '
                "variants are looked up next to the file (MyFont-Regular.ttf "
                "-> MyFont-Italic.ttf); missing styles use the regular file. "
                "The font must contain the characters of the agenda language."
            ),
            "cli": {"type": "str"},
        },
    )  # body text, labels, numbers
    title_padding: float = Field(
        2.0,
        ge=0,
        le=20,
        description="Side padding of title backgrounds, in mm.",
        json_schema_extra={
            "detail": (
                "Extra width, in mm, added on both sides of a title background "
                "(the weekend or holiday fill behind a day page header or a "
                "week page day row). The text stays aligned with the rest of "
                "the page; only the fill grows outward. 0 keeps the fill flush "
                "with the text."
            ),
            "cli": {},
        },
    )  # mm
    imposition: bool = Field(
        False,
        description="Export in booklet print order.",
        json_schema_extra={
            "detail": (
                "Export the pages in booklet print order, so the printed "
                "sheets can be folded into a booklet. It requires "
                "booklet_folded to be on and cannot be combined with spreads."
            ),
            "cli": {},
        },
    )
    crop_marks: bool = Field(
        False,
        description="Draw crop marks on the imposed or spread sheets.",
        json_schema_extra={
            "detail": (
                "Draw crop marks on the sheets to show where to cut. It "
                "requires imposition or spreads to be on, and the bleed "
                "setting controls the gap before each mark."
            ),
            "cli": {},
        },
    )
    spreads: bool = Field(
        False,
        description="Export as 2-up reader spreads.",
        json_schema_extra={
            "detail": (
                "Export the pages two per landscape sheet in reading order "
                "(page 1 alone on the right, then left and right pages "
                "together), to read or print as spreads. It cannot be "
                "combined with imposition. Crop marks and sheet_size apply to "
                "it."
            ),
            "cli": {},
        },
    )
    sheet_size: Literal["auto", "letter", "a4"] = Field(
        "auto",
        description="Sheet size for spreads and imposition.",
        json_schema_extra={
            "detail": (
                "Landscape sheet used by spreads and imposition: auto picks "
                "letter or A4, whichever scales the pages larger; letter or "
                "a4 forces it. Ignored for plain pages."
            ),
            "cli": {"type": "str"},
        },
    )
    output: Path = Field(
        Path("agenda.pdf"),
        description="Path of the exported PDF.",
        json_schema_extra={
            "detail": (
                "File path of the exported PDF. The file is written there "
                "when you use Export and is overwritten if it exists."
            ),
            "cli": {"flags": ["-o", "--output"]},
        },
    )
    debug_grid: bool = Field(
        False,
        description="Overlay margins, columns and baseline.",
        json_schema_extra={
            "detail": (
                "Overlay the margins, columns and baseline grid on every "
                "page. Use it to check the layout, and turn it off for the "
                "final print."
            ),
            "cli": {"flags": ["--debug-grid"]},
        },
    )

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
        from agenda.day_extras import load_dated, load_phrases

        if info.field_name == "daily_quotes_file":
            load_phrases(v)
        else:
            load_dated(v, 2000)
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
