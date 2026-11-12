"""Section registry: which Config field belongs to which settings section.

A grouping layer over the flat ``Config`` (it is never nested or renamed). Key mapping only: no
validation rules live here. Qt-free, and it imports neither ``Config`` nor pydantic.
Adding a section is a one-entry change to ``SECTIONS``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agenda import uitext

GLOBAL = "global"
PADDING = "padding"
MONTH_START = "month_start"
MONTH_END = "month_end"
STYLING = "styling"

ENABLE_KINDS = ("planner", "page", "count", "none")


@dataclass(frozen=True)
class SectionSpec:
    key: str
    label: str
    block: str | None  # nested YAML block name; None = no block
    fields: dict[str, str] = field(default_factory=dict)  # YAML short key -> Config field
    page_id: str | None = None
    enable: str = "none"  # "planner" | "page" | "count" | "none"
    count_field: str | None = None  # Config field for enable="count" (on = value > 0)


def _page(page_id: str, label: str) -> SectionSpec:
    """A catalog page with no settings, switched on and off through ``Config.pages``."""
    return SectionSpec(page_id, label, None, page_id=page_id, enable="page")


SECTIONS: tuple[SectionSpec, ...] = (
    SectionSpec(GLOBAL, "Global", None),
    # Which page fills the last booklet and how much; the pad page itself is set in its section.
    SectionSpec(
        PADDING,
        "Padding",
        "padding",
        {"pad_with": "pad_with", "extra_padding": "extra_padding"},
    ),
    # Per-month pages (BasePage.per_month) printed inside each month, picked by checkboxes.
    SectionSpec(MONTH_START, "Start of each month", MONTH_START, {"pages": "month_start_pages"}),
    SectionSpec(
        "daily",
        "Day pages",
        "daily",
        {
            "months": "daily_months",
            "hour_start": "daily_hour_start",
            "hour_end": "daily_hour_end",
            "holidays": "daily_holidays",
            "quotes": "daily_quotes",
            "quotes_file": "daily_quotes_file",
            "extra_file": "daily_extra_file",
            "filler": "daily_filler",
        },
        page_id="daily",
        enable="planner",
    ),
    SectionSpec(
        "weekly",
        "Week pages",
        "weekly",
        {"filler": "weekly_filler"},
        page_id="weekly",
        enable="planner",
    ),
    SectionSpec(MONTH_END, "End of each month", MONTH_END, {"pages": "month_end_pages"}),
    SectionSpec(
        "notes",
        "Notes",
        "notes",
        {"pattern": "notes_pattern", "pages": "notes_pages"},
        page_id="notes",
        enable="count",
        count_field="notes_pages",
    ),
    # Optional pages, then value-added pages, in catalog order; most have no settings of their own.
    SectionSpec(
        "contacts",
        "Contacts",
        "contacts",
        {"pages": "contacts_pages"},
        page_id="contacts",
        enable="count",
        count_field="contacts_pages",
    ),
    _page("budget", "Monthly budget"),
    _page("goals", "Yearly goals"),
    SectionSpec(
        "habits", "Habit tracker", "habits", {"max": "habits_max"}, page_id="habits", enable="page"
    ),
    _page("holidays", "Holidays"),
    _page("important_dates", "Important dates"),
    _page("monthly_review", "Monthly review"),
    _page("passwords", "Passwords"),
    _page("projects", "Project planner"),
    SectionSpec(
        "schedule",
        "Weekly schedule",
        "schedule",
        {"first_hour": "schedule_first_hour", "last_hour": "schedule_last_hour"},
        page_id="schedule",
        enable="page",
    ),
    _page("todo", "To-do list"),
    SectionSpec(
        "niche_entrepreneur",
        "Entrepreneur pack",
        "niche_entrepreneur",
        {"pages": "niche_entrepreneur_pages"},
        page_id="niche_entrepreneur",
        enable="page",
    ),
    SectionSpec(
        "niche_fitness",
        "Fitness pack",
        "niche_fitness",
        {"pages": "niche_fitness_pages"},
        page_id="niche_fitness",
        enable="page",
    ),
    SectionSpec(
        "niche_student",
        "Student pack",
        "niche_student",
        {"pages": "niche_student_pages"},
        page_id="niche_student",
        enable="page",
    ),
    _page("physical_extras", "Physical extras guide"),
    SectionSpec("qr", "QR codes", "qr", {"urls": "qr_urls"}, page_id="qr", enable="page"),
    _page("challenges30", "30-day challenges"),
    _page("gratitude", "Gratitude journal"),
    _page("health", "Health tracker"),
    _page("meals", "Meal and grocery planner"),
    _page("travel", "Travel planner"),
    _page("vision_board", "Vision board"),
    _page("ideas", "Idea map"),
    _page("media_log", "Books, movies and series"),
    _page("quotes", "Monthly quotes"),
    SectionSpec(
        STYLING,
        "PDF colors & fonts",
        "style",
        {
            "theme": "theme",
            "ink": "color_ink",
            "muted": "color_muted",
            "line": "color_line",
            "accent": "color_accent",
            "tint": "color_tint",
            "weekend_fill": "color_weekend_fill",
            "holiday_fill": "color_holiday_fill",
            "primary_font": "font_primary",
            "secondary_font": "font_secondary",
            "title_padding": "title_padding",
        },
    ),
)


@dataclass(frozen=True)
class GroupSpec:
    key: str
    label: str
    sections: tuple[str, ...]  # section keys, in display order


def _keys(start: str, stop: str) -> tuple[str, ...]:
    """Section keys from ``start`` up to and including ``stop``, in ``SECTIONS`` order."""
    keys = [s.key for s in SECTIONS]
    return tuple(keys[keys.index(start) : keys.index(stop) + 1])


# Settings tab-list grouping (GUI only; the YAML layout follows SECTIONS).
GROUPS: tuple[GroupSpec, ...] = (
    GroupSpec("general", "General", (GLOBAL, PADDING, STYLING)),
    GroupSpec("planner", "Planner pages", _keys(MONTH_START, "notes")),
    GroupSpec("optional", "Optional pages", _keys("contacts", "todo")),
    GroupSpec("value_added", "Value-added pages", _keys("niche_entrepreneur", "quotes")),
)

TEMPLATE_KEYS: tuple[str, ...] = tuple(s.key for s in SECTIONS if s.page_id)
# The GUI's "Whole agenda" tab (key GLOBAL) holds the sections without a page of their own; every
# template section gets a tab of its own.
WHOLE_SECTIONS: tuple[str, ...] = tuple(s.key for s in SECTIONS if not s.page_id)

_BY_KEY = {s.key: s for s in SECTIONS}


def section(key: str) -> SectionSpec:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise KeyError(f"unknown section {key!r}; valid: {', '.join(_BY_KEY)}") from None


def section_label(key: str) -> str:
    """Display label of a section in the current UI language (English from the spec)."""
    return uitext.lookup(f"section.{key}") or section(key).label


def tab_of(key: str) -> str:
    """GUI tab holding section ``key``: the template itself, or GLOBAL for the whole agenda."""
    section(key)
    return key if key in TEMPLATE_KEYS else GLOBAL


def tab_groups() -> list[tuple[str, tuple[str, ...]]]:
    """(group key, template keys) for each group with templates, in tab-list order."""
    out = []
    for g in GROUPS:
        keys = tuple(k for k in g.sections if k in TEMPLATE_KEYS)
        if keys:
            out.append((g.key, keys))
    return out


def group_label(key: str) -> str:
    """Display label of a settings-panel group in the current UI language."""
    for g in GROUPS:
        if g.key == key:
            return uitext.lookup(f"group.{key}") or g.label
    raise KeyError(f"unknown group {key!r}")


def group_of(field_name: str) -> str:
    for s in SECTIONS:
        if field_name in s.fields.values():
            return s.key
    return GLOBAL


def fields_of(key: str, all_fields: Any) -> list[str]:
    """Config fields of section ``key``, in the order of ``all_fields``; GLOBAL gets the rest."""
    section(key)
    return [f for f in all_fields if group_of(f) == key]


def is_enabled(cfg: Any, key: str) -> bool:
    s = section(key)
    if s.enable == "planner":
        return s.key in cfg.planners
    if s.enable == "page":
        return s.page_id in (cfg.pages or [])
    if s.enable == "count":
        return getattr(cfg, s.count_field) > 0
    return True


def has_enable_box(key: str) -> bool:
    return section(key).enable != "none"


def with_enabled(values: dict[str, Any], key: str, on: bool) -> dict[str, Any]:
    """Copy of the raw ``values`` with section ``key`` switched on or off."""
    s = section(key)
    if s.enable == "none":
        raise ValueError(f"section {key!r} has no enable switch")
    out = dict(values)
    if s.enable == "planner":
        planners = [p for p in out.get("planners") or [] if p != s.key]
        if on:
            order = ("weekly", "daily")
            planners = [p for p in order if p in planners or p == s.key]
        out["planners"] = planners
        return out
    if s.enable == "count":
        if not on:
            out[s.count_field] = 0
        elif not out.get(s.count_field, 1):
            out[s.count_field] = 1
        return out
    pages = list(out.get("pages") or [])
    if not pages and out.get("preset"):
        from agenda.catalog import preset_pages  # lazy: the catalog imports Config

        pages = list(preset_pages(out["preset"]))
    if on and s.page_id not in pages:
        pages.append(s.page_id)
    elif not on:
        pages = [p for p in pages if p != s.page_id]
    out["pages"] = pages
    return out
