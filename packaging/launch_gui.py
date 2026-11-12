"""PyInstaller entry point for the GUI (a plain script, so the package imports absolutely)."""

import sys

from agenda.gui.app import main

if __name__ == "__main__":
    sys.exit(main())
