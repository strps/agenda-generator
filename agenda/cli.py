"""typer command line: flags mirror the ``Config`` fields one to one.

The CLI only maps flags to ``Config`` keyword arguments (``build_overrides``); every rule is
enforced by the ``Config`` model, which is validated once in ``run``.
"""

import inspect
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from agenda import __version__
from agenda.config import Config
from agenda.configfile import load_yaml, merge
from agenda.exporter import DEFAULT_OUTPUT, FontsMissingError, export_agenda, export_blank
from agenda.fields import cli_meta, field_names, short_help
from agenda.uitext import tr

app = typer.Typer(add_completion=False, help=tr("cli.help"))


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
    month_start_pages: str | None = None,
    month_end_pages: str | None = None,
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
    for name, value in (
        ("month_start_pages", month_start_pages),
        ("month_end_pages", month_end_pages),
    ):
        if value is not None:
            out[name] = split_csv(value)
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
    typer.echo(tr("cli.error", message=message), err=True)
    return typer.Exit(code)


def _field_type(name: str) -> Any:
    """CLI type of a Config field: the ``cli`` type override, else its annotation minus None."""
    if cli_meta(name).get("type") == "str":
        return str
    annotation = Config.model_fields[name].annotation
    args = [a for a in getattr(annotation, "__args__", ()) if a is not type(None)]
    return args[0] if args else annotation


def _generated_params() -> list[inspect.Parameter]:
    """One keyword parameter per simple Config field, in field order (flags from ``cli`` meta)."""
    params = []
    for name in field_names():
        meta = cli_meta(name)
        if meta.get("skip"):
            continue
        kind = _field_type(name)
        dashed = name.replace("_", "-")
        flags = meta.get("flags") or [
            f"--{dashed}/--no-{dashed}" if kind is bool else f"--{dashed}"
        ]
        option = typer.Option(*flags, help=short_help(name))
        params.append(
            inspect.Parameter(
                name,
                inspect.Parameter.KEYWORD_ONLY,
                default=None,
                annotation=Annotated[kind | None, option],
            )
        )
    return params


def _hand_params() -> tuple[list[inspect.Parameter], list[inspect.Parameter]]:
    """Hand-written options: those before the generated ones, and those after."""

    def param(name: str, annotation: Any, default: Any) -> inspect.Parameter:
        return inspect.Parameter(
            name, inspect.Parameter.KEYWORD_ONLY, default=default, annotation=annotation
        )

    first = [
        param(
            "version",
            Annotated[
                bool,
                typer.Option("--version", callback=_version, is_eager=True, help=tr("cli.version")),
            ],
            False,
        ),
        param(
            "list_pages",
            Annotated[
                bool,
                typer.Option("--list", callback=_list, is_eager=True, help=tr("cli.list")),
            ],
            False,
        ),
        param(
            "config",
            Annotated[Path | None, typer.Option("--config", help=tr("cli.config"))],
            None,
        ),
    ]
    last = [
        param("pages", Annotated[str | None, typer.Option(help=short_help("pages"))], None),
        param(
            "qr_url",
            Annotated[list[str] | None, typer.Option("--qr-url", help=short_help("qr_urls"))],
            None,
        ),
        param(
            "category",
            Annotated[
                str | None,
                typer.Option(help=tr("cli.category")),
            ],
            None,
        ),
        param(
            "page_range",
            Annotated[
                str | None,
                typer.Option(
                    "--page-range",
                    help=tr("cli.page_range"),
                ),
            ],
            None,
        ),
        param(
            "blank_pages",
            Annotated[
                int | None,
                typer.Option(help=tr("cli.blank_pages")),
            ],
            None,
        ),
        param(
            "dry_run",
            Annotated[bool, typer.Option("--dry-run", help=tr("cli.dry_run"))],
            False,
        ),
    ]
    return first, last


_HAND_NAMES = {
    "version",
    "list_pages",
    "config",
    "pages",
    "qr_url",
    "category",
    "page_range",
    "blank_pages",
    "dry_run",
}


def run(**opts: Any) -> None:
    """Build the config from the flags, validate it once and write the PDF.

    The signature (one option per Config field) is generated below from ``agenda.fields``.
    """
    config = opts["config"]
    page_range = opts["page_range"]
    blank_pages = opts["blank_pages"]
    dry_run = opts["dry_run"]
    try:
        overrides = build_overrides(
            pages=opts["pages"],
            category=opts["category"],
            qr_url=opts["qr_url"],
            **{k: v for k, v in opts.items() if k not in _HAND_NAMES},
        )
        merged = merge(load_yaml(config) if config is not None else {}, overrides)
        cfg = Config(**merged)
    except ValueError as exc:
        raise _fail(str(exc), 2) from None
    from agenda import themes

    if not themes.is_known(cfg.theme):
        typer.echo(
            tr("cli.unknown_theme", theme=repr(cfg.theme), known=", ".join(themes.THEMES)),
            err=True,
        )
    if dry_run:
        from agenda.assembler import build_plan, summarize

        typer.echo(summarize(build_plan(cfg), cfg).format())
        raise typer.Exit()
    target = cfg.output if "output" in merged else DEFAULT_OUTPUT
    pages = None
    if page_range is not None:
        from agenda.assembler import build_plan
        from agenda.pagerange import parse_page_range

        try:
            if cfg.imposition or cfg.spreads:
                raise ValueError(tr("cli.range_singles_only"))
            pages = parse_page_range(page_range, len(build_plan(cfg)))
        except ValueError as exc:
            raise _fail(tr("cli.page_range_error", message=exc), 2) from None
    try:
        if blank_pages is None:
            out = (
                export_agenda(cfg, target)
                if pages is None
                else export_agenda(cfg, target, pages=pages)
            )
        else:
            out = export_blank(cfg, blank_pages, target)
    except FontsMissingError as exc:
        raise _fail(str(exc), 1) from None
    typer.echo(tr("cli.wrote", path=out))


_first, _last = _hand_params()
_params = [*_first, *_generated_params(), *_last]
run.__signature__ = inspect.Signature(_params, return_annotation=None)  # type: ignore[attr-defined]
run.__annotations__ = {p.name: p.annotation for p in _params} | {"return": None}
app.command(help=tr("cli.help"))(run)


def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the exit code (used by the entry point and by tests)."""
    try:
        app(args=argv, prog_name="agenda-gen")
    except SystemExit as exc:  # standalone mode exits; keep the code for callers and tests
        return exc.code if isinstance(exc.code, int) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
