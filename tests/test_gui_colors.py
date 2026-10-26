import os
import re

import pytest

from agenda.gui import bar_model as B
from agenda.gui import section_colors as C

SECTIONS = ["front_back", "monthly", "weekly", "daily", "optional", "value_added"]
HEX = re.compile(r"^#[0-9a-f]{6}$")


def test_covers_every_section_and_padding():
    assert set(C.PALETTE) == {*SECTIONS, B.PADDING}


def test_page_classes_only_use_known_sections():
    from agenda.pages import core, optional, value_added

    found = set()
    for mod in (core, optional, value_added):
        for obj in vars(mod).values():
            s = getattr(obj, "section", None)
            if isinstance(s, str):
                found.add(s)
    assert found <= set(C.PALETTE)


@pytest.mark.parametrize("dark", [False, True])
def test_valid_and_distinct_hues(dark):
    colors = {k: C.section_color(k, dark) for k in SECTIONS}
    assert all(HEX.match(c) for c in colors.values())
    assert len(set(colors.values())) == len(SECTIONS)
    assert C.section_color(B.PADDING, dark) == C.GRAY


def test_spec_values():
    assert C.section_color("monthly", False) == "#2a78d6"
    assert C.section_color("monthly", True) == "#3987e5"
    assert C.section_color("value_added", True) == "#c98500"
    assert C.section_color("front_back", True) == C.section_color("front_back", False)


def test_unknown_key_falls_back_to_gray():
    assert C.section_color("nope", True) == C.GRAY


def test_is_dark():
    assert C.is_dark(30) and not C.is_dark(240)


@pytest.mark.gui
def test_bar_uses_palette():
    pytest.importorskip("PySide6")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtWidgets import QApplication

    from agenda.gui.section_bar import SectionBar

    QApplication.instance() or QApplication([])
    bar = SectionBar()
    assert bar.color_for("weekly").name() == bar.color_for("weekly").name()
    assert bar.color_for("monthly").name() in ("#2a78d6", "#3987e5")
