import subprocess
import sys
from pathlib import Path

import pytest

from agenda.gui import help_text
from agenda.gui.bar_model import SECTION_LABELS
from agenda.gui.help_text import (
    SECTION_DESCRIPTIONS,
    TOOLTIPS,
    section_tooltip,
)

IDS = ["open_config", "save_config", "export_pdf", "prev", "next",
       "mode_single", "mode_spread", "mode_sheet", "zoom"]


@pytest.mark.parametrize("key", IDS)
def test_tooltip_detailed(key):
    text = TOOLTIPS[key]
    assert len(text) >= 40
    assert "." in text


def test_disabled_reason():
    assert help_text.EXPORT_DISABLED_REASON.strip()


def test_descriptions_cover_sections():
    assert set(SECTION_DESCRIPTIONS) == set(SECTION_LABELS)


def test_section_tooltip():
    t = section_tooltip("padding").lower()
    assert t.startswith("padding:")
    assert "filler" in t or "blank" in t
    assert section_tooltip("nope") == "nope"


def test_no_qt_import():
    assert "PySide6" not in Path(help_text.__file__).read_text()
    code = "import sys, agenda.gui.help_text; assert not any(m.startswith('PySide6') for m in sys.modules)"
    subprocess.run([sys.executable, "-c", code], check=True)
