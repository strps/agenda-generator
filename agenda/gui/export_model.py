"""Qt-free export helpers: default destination and progress fraction."""

from __future__ import annotations

import shlex
from pathlib import Path
from typing import Any, Mapping

from agenda.config import Config

EXPORT_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Page numbers",
        (
            "page_numbers",
            "page_number_start",
            "page_number_first",
            "page_number_position",
            "page_number_placement",
            "page_number_format",
        ),
    ),
    ("Layout", ("imposition", "spreads", "sheet_size", "crop_marks", "bleed")),
    (
        "Booklets",
        ("booklet_size", "booklet_unit", "booklet_folded", "num_booklets", "separate_covers"),
    ),
    ("Output", ("output", "debug_grid")),
)

LAYOUTS = ("pages", "spreads", "booklets")

_CLI_FLAGS: dict[str, str] = {"booklet_folded": "--folded", "output": "--output"}
# Bool options declared with an explicit name and no "/" have no negative form.
_NO_NEGATIVE = {"debug_grid"}


def export_field_names() -> list[str]:
    return [f for _, fields in EXPORT_FIELDS for f in fields]


def layout_of(values: Mapping[str, Any]) -> str:
    if values.get("imposition"):
        return "booklets"
    if values.get("spreads"):
        return "spreads"
    return "pages"


def with_layout(values: Mapping[str, Any], layout: str) -> dict[str, Any]:
    """Copy of ``values`` switched to ``layout`` (booklets force folded imposition)."""
    if layout not in LAYOUTS:
        raise ValueError(f"unknown layout: {layout}")
    out = dict(values)
    out["imposition"] = layout == "booklets"
    out["spreads"] = layout == "spreads"
    if layout == "booklets":
        out["booklet_folded"] = True
    return out


def field_enabled(values: Mapping[str, Any], name: str) -> bool:
    """Whether the editor for ``name`` (or ``page_range``) accepts input."""
    layout = layout_of(values)
    if name.startswith("page_number_"):
        return bool(values.get("page_numbers"))
    if name in ("sheet_size", "crop_marks"):
        return layout != "pages"
    if name == "bleed":
        return layout != "pages" and bool(values.get("crop_marks"))
    if name == "booklet_folded":
        return layout != "booklets"
    if name == "page_range":
        return layout == "pages"
    return True


def default_path(cfg: Config) -> str:
    """Suggested destination for the save dialog: ``cfg.output`` (a .pdf suffix is ensured)."""
    return str(ensure_pdf(cfg.output))


def ensure_pdf(path: str | Path) -> Path:
    p = Path(path)
    return p if p.suffix.lower() == ".pdf" else p.with_suffix(p.suffix + ".pdf")


def progress_fraction(done: int, total: int) -> float:
    """``done / total`` clamped to 0..1; 0 when total is not positive."""
    if total <= 0:
        return 0.0
    return min(max(done / total, 0.0), 1.0)


def progress_percent(done: int, total: int) -> int:
    return round(progress_fraction(done, total) * 100)


def validate(values: Mapping[str, Any], page_range: str = "") -> str:
    """Empty string when ``values`` and ``page_range`` can be exported, else the error text."""
    from agenda.assembler import build_plan
    from agenda.gui.settings_model import build_config
    from agenda.pagerange import parse_page_range

    cfg, err = build_config(dict(values))
    if cfg is None:
        return err
    if (page_range or "").strip().lower() not in ("", "all"):
        if cfg.imposition or cfg.spreads:
            return "page range: a page range can only be exported as single pages"
        try:
            parse_page_range(page_range, len(build_plan(cfg)))
        except ValueError as exc:
            return f"page range: {exc}"
    return ""


def _flag(name: str) -> str:
    return _CLI_FLAGS.get(name, "--" + name.replace("_", "-"))


def cli_args(
    values: Mapping[str, Any],
    page_range: str = "",
    defaults: Mapping[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> list[str]:
    """CLI arguments equivalent to the export fields that differ from ``defaults``."""
    if defaults is None:
        from agenda.gui.settings_model import default_values

        defaults = default_values()
    args: list[str] = []
    if config_path is not None:
        args += ["--config", str(config_path)]
    for name in export_field_names():
        if name not in values:
            continue
        value, default = values[name], defaults.get(name)
        if value == default or (name == "output" and str(value) == str(default)):
            continue
        if isinstance(value, bool):
            if name == "booklet_folded":
                args.append("--folded" if value else "--flat")
            elif value:
                args.append(_flag(name))
            elif name not in _NO_NEGATIVE:
                args.append("--no-" + name.replace("_", "-"))
        else:
            args += [_flag(name), str(value)]
    text = (page_range or "").strip()
    if text and text.lower() != "all":
        args += ["--page-range", text]
    return args


def cli_command(
    values: Mapping[str, Any],
    page_range: str = "",
    defaults: Mapping[str, Any] | None = None,
    config_path: str | Path | None = None,
) -> str:
    return shlex.join(["agenda-gen", *cli_args(values, page_range, defaults, config_path)])
