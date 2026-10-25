"""Command-line entry point (`agenda-gen` / `python -m agenda`); the CLI lives in agenda.cli."""

import sys

from agenda.cli import main

if __name__ == "__main__":
    sys.exit(main())
