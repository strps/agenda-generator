"""typer command line: flags mirror the ``Config`` fields one to one.

The CLI only maps flags to ``Config`` keyword arguments (``build_overrides``); every rule is
enforced by the ``Config`` model, which is validated once in ``run``.
"""

import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from agenda import __version__
from agenda.config import Config
from agenda.configfile import load_yaml, merge
from agenda.exporter import DEFAULT_OUTPUT, FontsMissingError, export_agenda, export_blank

app = typer.Typer(add_completion=False, help="Generate a printable agenda PDF.")


def split_csv(value: str | None) -> list[str] | None:
    """``"a, b,,c"`` -> ``["a", "b", "c"]``; ``None`` stays ``None``."""
    if value is None:
        return None
    return [part.strip() for part in value.split(",") if part.strip()]


def build_overrides(
    *,
    pages: str | None = None,
    category: str | None = None,
    planners: str | None = None,
    qr_url: list[str] | None = None,
    num_booklets: str | None = None,
    **fields: Any,
) -> dict[str, Any]:
    """Map flag values to ``Config`` kwargs; ``None`` (flag not given) is dropped.

    ``pages`` and ``category`` (comma lists of page ids / categories) are merged into one ordered,
    de-duplicated ``pages`` list. Values are not checked here: ``Config`` does that.
    """
    out = {k: v for k, v in fields.items() if v is not None}
    ids = split_csv(pages) or []
    if category is not None:
        from agenda.catalog import pages_by_category

        for cat in split_csv(category) or []:
            ids += [p.id for p in pages_by_category(cat)]
    if pages is not None or category is not None:
        out["pages"] = list(dict.fromkeys(ids))
    if planners is not None:
        out["planners"] = split_csv(planners)
    if qr_url:
        out["qr_urls"] = list(qr_url)
    if num_booklets is not None:
        out["num_booklets"] = int(num_booklets) if num_booklets.strip().isdigit() else num_booklets
    return out


def _version(value: bool) -> None:
    if value:
        typer.echo(f"agenda-gen {__version__}")
        raise typer.Exit()


def _list(value: bool) -> None:
    if value:
        from agenda.catalog import catalog_rows, format_catalog

        typer.echo(format_catalog(catalog_rows()))
        raise typer.Exit()


def _fail(message: str, code: int) -> "typer.Exit":
    typer.echo(f"agenda-gen: {message}", err=True)
    return typer.Exit(code)


@app.command()
def run(
    version: Annotated[
        bool, typer.Option("--version", callback=_version, is_eager=True, help="Show version.")
    ] = False,
    list_pages: Annotated[
        bool,
        typer.Option("--list", callback=_list, is_eager=True, help="List the page catalog."),
    ] = False,
    config: Annotated[
        Path | None, typer.Option("--config", help="YAML settings file; flags override it.")
    ] = None,
    # Page geometry
    page_size: Annotated[
        str | None, typer.Option("--page-size", "--size", help="Named size or WxH in mm.")
    ] = None,
    orientation: Annotated[str | None, typer.Option(help="portrait or landscape.")] = None,
    inner_margin: Annotated[float | None, typer.Option(help="Binding-side margin, mm.")] = None,
    outer_margin: Annotated[float | None, typer.Option(help="Outer margin, mm.")] = None,
    bleed: Annotated[float | None, typer.Option(help="Bleed, mm (with crop marks).")] = None,
    # Booklets
    booklet_size: Annotated[
        int | None, typer.Option("--booklet-size", "--booklet", help="Booklet size.")
    ] = None,
    booklet_unit: Annotated[
        str | None, typer.Option("--booklet-unit", "--unit", help="sheets or pages.")
    ] = None,
    booklet_folded: Annotated[
        bool | None, typer.Option("--folded/--flat", help="Folded or flat booklets.")
    ] = None,
    num_booklets: Annotated[str | None, typer.Option(help="Number of booklets or auto.")] = None,
    pad_with: Annotated[str | None, typer.Option(help="Page id used as padding.")] = None,
    separate_covers: Annotated[
        bool | None, typer.Option("--separate-covers/--no-separate-covers")
    ] = None,
    creep_mm: Annotated[float | None, typer.Option(help="Creep compensation, mm.")] = None,
    # Content
    planners: Annotated[str | None, typer.Option(help="Comma list: weekly,daily.")] = None,
    daily_months: Annotated[
        str | None, typer.Option(help='Months with daily pages, e.g. "1-6,9".')
    ] = None,
    daily_hour_start: Annotated[
        int | None, typer.Option(help="First hour (0-23) on day pages.")
    ] = None,
    daily_hour_end: Annotated[
        int | None, typer.Option(help="Last hour (0-23) on day pages.")
    ] = None,
    schedule_first_hour: Annotated[
        int | None, typer.Option(help="First hour (0-23) of the weekly schedule.")
    ] = None,
    schedule_last_hour: Annotated[
        int | None, typer.Option(help="Last hour (0-23) of the weekly schedule.")
    ] = None,
    habits_max: Annotated[
        int | None, typer.Option(help="Maximum habit rows on the habit tracker (1-40).")
    ] = None,
    niche_entrepreneur_pages: Annotated[
        int | None, typer.Option(help="Pages of the entrepreneur pack (1-20).")
    ] = None,
    niche_student_pages: Annotated[
        int | None, typer.Option(help="Pages of the student pack (1-20).")
    ] = None,
    niche_fitness_pages: Annotated[
        int | None, typer.Option(help="Pages of the fitness pack (1-20).")
    ] = None,
    notes_pages: Annotated[
        int | None, typer.Option(help="Back-matter Notes pages (0-50; 0 removes them).")
    ] = None,
    contacts_pages: Annotated[
        int | None, typer.Option(help="Back-matter Contacts pages (0-50; 0 removes them).")
    ] = None,
    extra_padding: Annotated[
        int | None, typer.Option(help="Minimum number of padding units (0-200).")
    ] = None,
    pages: Annotated[str | None, typer.Option(help="Comma list of catalog page ids.")] = None,
    category: Annotated[
        str | None, typer.Option(help="Comma list of categories: core,optional,value_added.")
    ] = None,
    preset: Annotated[str | None, typer.Option(help="essential, complete or premium.")] = None,
    notes_pattern: Annotated[str | None, typer.Option(help="lined, dotted, grid or blank.")] = None,
    page_numbers: Annotated[bool | None, typer.Option("--page-numbers/--no-page-numbers")] = None,
    qr_url: Annotated[
        list[str] | None, typer.Option("--qr-url", help="Text or URL for the qr page (repeat).")
    ] = None,
    # Calendar / locale
    year: Annotated[int | None, typer.Option(help="Calendar year.")] = None,
    week_start: Annotated[str | None, typer.Option(help="monday or sunday.")] = None,
    language: Annotated[str | None, typer.Option(help="es or en.")] = None,
    holiday_country: Annotated[str | None, typer.Option(help="Country code, e.g. CR.")] = None,
    # Look & output
    theme: Annotated[str | None, typer.Option(help="Theme name.")] = None,
    imposition: Annotated[bool | None, typer.Option("--imposition/--no-imposition")] = None,
    crop_marks: Annotated[bool | None, typer.Option("--crop-marks/--no-crop-marks")] = None,
    output: Annotated[
        Path | None, typer.Option("-o", "--output", help="Output PDF (default output/agenda.pdf).")
    ] = None,
    debug_grid: Annotated[
        bool | None, typer.Option("--debug-grid", help="Overlay margins, columns and baseline.")
    ] = None,
    blank_pages: Annotated[
        int | None, typer.Option(help="Write N blank pages instead of the agenda (temporary).")
    ] = None,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Print the plan summary; render nothing.")
    ] = False,
) -> None:
    """Build the config from the flags, validate it once and write the PDF."""
    try:
        overrides = build_overrides(
            pages=pages,
            category=category,
            planners=planners,
            qr_url=qr_url,
            num_booklets=num_booklets,
            page_size=page_size,
            orientation=orientation,
            inner_margin=inner_margin,
            outer_margin=outer_margin,
            bleed=bleed,
            booklet_size=booklet_size,
            booklet_unit=booklet_unit,
            booklet_folded=booklet_folded,
            pad_with=pad_with,
            separate_covers=separate_covers,
            creep_mm=creep_mm,
            daily_months=daily_months,
            daily_hour_start=daily_hour_start,
            daily_hour_end=daily_hour_end,
            schedule_first_hour=schedule_first_hour,
            schedule_last_hour=schedule_last_hour,
            habits_max=habits_max,
            niche_entrepreneur_pages=niche_entrepreneur_pages,
            niche_student_pages=niche_student_pages,
            niche_fitness_pages=niche_fitness_pages,
            notes_pages=notes_pages,
            contacts_pages=contacts_pages,
            extra_padding=extra_padding,
            preset=preset,
            notes_pattern=notes_pattern,
            page_numbers=page_numbers,
            year=year,
            week_start=week_start,
            language=language,
            holiday_country=holiday_country,
            theme=theme,
            imposition=imposition,
            crop_marks=crop_marks,
            output=output,
            debug_grid=debug_grid,
        )
        merged = merge(load_yaml(config) if config is not None else {}, overrides)
        cfg = Config(**merged)
    except ValueError as exc:
        raise _fail(str(exc), 2) from None
    if dry_run:
        from agenda.assembler import build_plan, summarize

        typer.echo(summarize(build_plan(cfg), cfg).format())
        raise typer.Exit()
    target = cfg.output if "output" in merged else DEFAULT_OUTPUT
    try:
        if blank_pages is None:
            out = export_agenda(cfg, target)
        else:
            out = export_blank(cfg, blank_pages, target)
    except FontsMissingError as exc:
        raise _fail(str(exc), 1) from None
    typer.echo(f"wrote {out}")


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the exit code (used by the entry point and by tests)."""
    try:
        app(args=argv, prog_name="agenda-gen")
    except SystemExit as exc:  # standalone mode exits; keep the code for callers and tests
        return exc.code if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
