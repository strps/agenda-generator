"""Skip Qt-only test files at collection when PySide6 is not installed.

Files that are entirely Qt tests declare `pytestmark = pytest.mark.gui`. Their module-level
`from PySide6 ...` imports would otherwise error (or skip noisily) even under `-m "not gui"`.
"""

import importlib.util
from pathlib import Path

_HAS_QT = importlib.util.find_spec("PySide6") is not None


def pytest_ignore_collect(collection_path: Path, config):
    if _HAS_QT or collection_path.suffix != ".py":
        return None
    if "pytestmark = pytest.mark.gui" in collection_path.read_text(encoding="utf-8"):
        return True
    return None
