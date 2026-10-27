"""Qt-free sample plans for per-template previews, and which preview the main window shows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from agenda.assembler import PagePlan, PlanEntry, make_entry
from agenda.catalog import get_page
from agenda.config import Config
from agenda.grid import side_for_page
from agenda.gui import preview_model
from agenda.templates import (
    GLOBAL,
    MONTH_END,
    MONTH_START,
    PADDING,
    SECTIONS,
    STYLING,
    TEMPLATE_KEYS,
    section,
    section_label,
)
from agenda.uitext import Table, tr

PLACEHOLDER_URLS = ["https://example.com"]


def _ctx(cfg: Config, key: str, instance: int) -> dict[str, Any]:
    cls = get_page(section(key).page_id)
    if key == "qr" and not cfg.qr_urls:
        return {"urls": list(PLACEHOLDER_URLS)}
    ctxs = cls().instances(cfg)
    if key == "daily":
        months = set(cfg.daily_months)
        ctxs = [c for c in ctxs if c["date"].month in months] or ctxs
        return dict(ctxs[0])
    if not ctxs:
        return {}
    return dict(ctxs[max(0, min(instance, len(ctxs) - 1))])


def sample_plan(cfg: Config, key: str, instance: int = 0) -> PagePlan:
    """A small valid plan holding one instance of template ``key`` (a disabled one still works)."""
    if key not in TEMPLATE_KEYS:
        raise ValueError(f"no sample plan for section {key!r}; valid: {', '.join(TEMPLATE_KEYS)}")
    cls = get_page(section(key).page_id)
    ctx = _ctx(cfg, key, instance)
    entries: list[PlanEntry] = []
    want = cls.starts_on
    if want != "any" and side_for_page(1) != want:
        entries.append(make_entry(None, {}, 1, cls.section, booklet_index=1, kind="filler"))
    for k in range(cls.pages):
        entries.append(
            make_entry(cls, ctx, len(entries) + 1, cls.section, booklet_index=1, page_in_instance=k)
        )
    return PagePlan(tuple(entries))


def preview_mode(key: str) -> str:
    """Spread for two-page templates, else single."""
    cls = get_page(section(key).page_id)
    return preview_model.SPREAD if cls.pages == 2 else preview_model.SINGLE


def preview_target(active: str, last_template: str | None) -> str:
    """Key of the preview to show: a template shows itself, STYLING keeps the last template."""
    if active == STYLING:
        return last_template or GLOBAL
    return active


# Fields that print another section's page as padding or filler: field -> (owning section, use).
# A page id field, or a list of them for the month placements.
PAD_FIELDS: dict[str, tuple[str, str]] = {
    "pad_with": (PADDING, "pads the last booklet"),
    "weekly_filler": ("weekly", "fills the slot before a week spread"),
    "daily_filler": ("daily", "fills the slot after a week's day pages"),
    "month_start_pages": (MONTH_START, "printed after each monthly page"),
    "month_end_pages": (MONTH_END, "printed after each month's last week"),
}
PAD_SHORT: Mapping[str, str] = Table("pad.short", tuple(PAD_FIELDS))
MONTH_FIELDS = ("month_start_pages", "month_end_pages")
FILLER_TEXT: Mapping[str, str] = Table("filler", ("blank", "none"))


def section_of_page(page_id: str) -> str | None:
    """Key of the section that configures catalog page ``page_id`` (None: it has no section)."""
    return next((s.key for s in SECTIONS if s.page_id == page_id), None)


def pad_roles(values: dict[str, Any]) -> dict[str, list[str]]:
    """Section key -> the ``PAD_FIELDS`` that use its page, in ``PAD_FIELDS`` order."""
    out: dict[str, list[str]] = {}
    for name in PAD_FIELDS:
        value = values.get(name) or []
        for page_id in value if isinstance(value, list) else [value]:
            key = section_of_page(str(page_id))
            if key is not None:
                out.setdefault(key, []).append(name)
    return out


def pad_label(fields: list[str]) -> str:
    """Short header badge, e.g. "padding · month end" ("" when unused)."""
    return " · ".join(PAD_SHORT[f] for f in fields)


def pad_text(fields: list[str]) -> str:
    """One line per use: "Padding: pads the last booklet (set in Padding)."."""
    return "\n".join(
        tr(
            "pad.text",
            short=PAD_SHORT[f].capitalize(),
            use=tr(f"pad.use.{f}"),
            section=section_label(PAD_FIELDS[f][0]),
        )
        for f in fields
    )


def page_text(page_id: str) -> str:
    """What a catalog page is: "Notes: core page, 1 page, set up in its Notes section."."""
    cls = get_page(page_id)
    if cls.pages == 2:
        size = tr("page.size.spread")
    else:
        size = tr("page.size.many" if cls.pages > 1 else "page.size.one", n=cls.pages)
    key = section_of_page(page_id)
    repeat = tr("page.per_month") if cls.per_month else ""
    where = tr("page.where", section=section_label(key)) if key else ""
    category = tr(f"page.category.{cls.category}")
    return tr("page.text", name=cls.name, category=category, size=size, repeat=repeat, where=where)


def choice_tooltip(value: str) -> str:
    """Tooltip of one item of a page select (a filler mode or a page id)."""
    return FILLER_TEXT.get(value) or page_text(value)


def header_tooltip(key: str, fields: list[str]) -> str:
    """Tooltip of a template section header: the page, its enable box, then its pad uses."""
    s = section(key)
    lines = [page_text(s.page_id)] if s.page_id else []
    if s.enable == "count":
        lines.append(tr("header.count", field=s.count_field))
    elif s.enable != "none":
        lines.append(tr("header.enable"))
    if s.page_id and get_page(s.page_id).per_month and not any(f in MONTH_FIELDS for f in fields):
        lines.append(tr("header.month_hint"))
    if fields:
        lines.append(pad_text(fields))
        lines.append(tr("header.ringed"))
    if any(f in MONTH_FIELDS for f in fields):
        lines.append(tr("header.month_note"))
    return "\n".join(lines)
