"""Section registry: which Config field belongs to which settings section.

A grouping layer over the flat ``Config`` (it is never nested or renamed). Key mapping only: no
validation rules live here. Qt-free, and it imports neither ``Config`` nor pydantic.
Adding a section is a one-entry change to ``SECTIONS``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

GLOBAL = "global"
STYLING = "styling"

ENABLE_KINDS = ("planner", "page", "none")


@dataclass(frozen=True)
class SectionSpec:
    key: str
    label: str
    block: str | None  # nested YAML block name; None = no block
    fields: dict[str, str] = field(default_factory=dict)  # YAML short key -> Config field
    page_id: str | None = None
    enable: str = "none"  # "planner" | "page" | "none"


SECTIONS: tuple[SectionSpec, ...] = (
    SectionSpec(GLOBAL, "Global", None),
    SectionSpec(
        "notes",
        "Notes & padding",
        "notes",
        {"pattern": "notes_pattern", "pad_with": "pad_with"},
        page_id="notes",
    ),
    SectionSpec(
        "daily", "Day pages", "daily", {"months": "daily_months"}, page_id="daily", enable="planner"
    ),
    SectionSpec("weekly", "Week pages", None, {}, page_id="weekly", enable="planner"),
    SectionSpec("qr", "QR codes", "qr", {"urls": "qr_urls"}, page_id="qr", enable="page"),
    SectionSpec(STYLING, "Colors & styling", "style", {"theme": "theme"}),
)

TEMPLATE_KEYS: tuple[str, ...] = tuple(s.key for s in SECTIONS if s.page_id)

_BY_KEY = {s.key: s for s in SECTIONS}


def section(key: str) -> SectionSpec:
    try:
        return _BY_KEY[key]
    except KeyError:
        raise KeyError(f"unknown section {key!r}; valid: {', '.join(_BY_KEY)}") from None


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
