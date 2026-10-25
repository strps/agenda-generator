"""Command-line entry point (`agenda-gen` / `python -m agenda`).

Stub: later tasks add config loading, --debug-grid and PDF output.
"""

from __future__ import annotations

import argparse
import sys

from agenda import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agenda-gen", description="Generate a printable agenda PDF.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    build_parser().parse_args(argv)
    print("agenda-gen: not implemented yet", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
