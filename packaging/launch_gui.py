"""PyInstaller entry point for the GUI (a plain script, so the package imports absolutely).

``--self-test`` runs ``self_test.run`` instead of opening the window (used by CI).
"""

import sys

if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        import self_test

        sys.exit(self_test.run())
    from agenda.gui.app import main

    sys.exit(main())
