"""Command-line entry point (`agenda-gen` / `python -m agenda`).

Stub: later tasks add config loading, --debug-grid and PDF output.
"""

from __future__ import annotations

import argparse
import sys

from agenda import __version__
from agenda.config import Config
from agenda.exporter import DEFAULT_OUTPUT, FontsMissingError, export_blank


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agenda-gen", description="Generate a printable agenda PDF."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "-o", "--output", default=None, help="output PDF path (default output/agenda.pdf)"
    )
    parser.add_argument("--pages", type=int, default=4, help="number of blank pages (temporary)")
    parser.add_argument("--page-size", default=None, help="named size or WxH in mm")
    parser.add_argument("--orientation", choices=["portrait", "landscape"], default=None)
    parser.add_argument(
        "--debug-grid", action="store_true", help="overlay margins, columns, baseline and rulers"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    overrides = {
        k: v for k, v in (("page_size", args.page_size), ("orientation", args.orientation)) if v
    }
    if args.debug_grid:
        overrides["debug_grid"] = True
    try:
        cfg = Config(**overrides)
    except ValueError as exc:
        print(f"agenda-gen: {exc}", file=sys.stderr)
        return 2
    try:
        out = export_blank(cfg, args.pages, args.output or DEFAULT_OUTPUT)
    except FontsMissingError as exc:
        print(f"agenda-gen: {exc}", file=sys.stderr)
        return 1
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
