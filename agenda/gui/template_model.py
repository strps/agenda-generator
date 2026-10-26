"""Qt-free sample plans for per-template previews, and which preview the main window shows."""

from __future__ import annotations

from typing import Any

from agenda.assembler import PagePlan, PlanEntry, make_entry
from agenda.catalog import get_page
from agenda.config import Config
from agenda.gui import preview_model
from agenda.grid import side_for_page
from agenda.templates import GLOBAL, STYLING, TEMPLATE_KEYS, section

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
