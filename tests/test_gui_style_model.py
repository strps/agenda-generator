import re

import pytest

from agenda.gui import style_model as S

TOKENS = S.REQUIRED_TOKENS
HEX = re.compile(r"^#[0-9a-f]{6}$")


def test_tokens_complete_and_hex():
    assert set(S.THEMES) == {"dark", "light"}
    for t in S.THEMES.values():
        for k in TOKENS:
            assert HEX.match(t[k]), k
    assert S.stylesheet(True) != S.stylesheet(False)


def test_resolve_dark():
    assert S.resolve_dark("light", 0) is False
    assert S.resolve_dark("dark", 255) is True
    assert S.resolve_dark("system", 20) is True
    assert S.resolve_dark("system", 240) is False
    assert S.resolve_dark("bogus", 255) is True
    assert S.DEFAULT_APPEARANCE == "dark"
    assert S.APPEARANCES == ("dark", "light", "system")


def test_contrast_ratio_known_values():
    assert S.contrast_ratio("#000000", "#ffffff") == pytest.approx(21)
    assert S.contrast_ratio("#777777", "#777777") == pytest.approx(1)


@pytest.mark.parametrize("name", ["dark", "light"])
def test_contrast(name):
    t = S.THEMES[name]
    c = S.contrast_ratio
    assert c(t["text"], t["window"]) >= 7
    assert c(t["text"], t["panel"]) >= 4.5
    assert c(t["accent_text"], t["accent"]) >= 4.5
    assert c(t["tooltip_text"], t["tooltip_bg"]) >= 4.5
    assert c(t["error"], t["panel"]) >= 4.5
    assert c(t["muted"], t["panel"]) >= 3


SELECTORS = [
    "QMainWindow", "QPushButton", "QPushButton:hover", "QPushButton:pressed",
    "QPushButton:disabled", "QPushButton:checked", "QPushButton#export_button",
    "QLineEdit", "QSpinBox", "QDoubleSpinBox", "QComboBox", "QPlainTextEdit",
    "QLineEdit:disabled", "QComboBox:disabled", "QGroupBox", "QGroupBox::title",
    'QFrame[objectName^="section_"]', "QPushButton#section_toggle",
    "QCheckBox#section_enable", "QScrollArea", "QToolTip", "QProgressBar",
    "QProgressBar::chunk", "QLabel#settings_error", "QLabel#legend_title",
    'QLabel[objectName^="template_notice_"]',
]  # fmt: skip


@pytest.mark.parametrize("dark", [True, False])
def test_stylesheet_selectors(dark):
    qss = S.stylesheet(dark)
    for sel in SELECTORS:
        assert sel in qss, sel
    assert not re.search(r"(^|[},\s])QLabel\s*\{", qss)


@pytest.mark.parametrize("dark", [True, False])
def test_minimalism(dark):
    qss = S.stylesheet(dark)
    assert "gradient" not in qss.lower()
    for decl in re.findall(r"border(?:-width)?\s*:[^;]*;", qss):
        for w in re.findall(r"(\d+)px", decl):
            assert int(w) <= 1, decl
    assert not re.search(r"outset|inset|ridge|groove|double", qss)
    assert "box-shadow" not in qss
    assert len(set(re.findall(r"#[0-9a-fA-F]{6}", qss))) <= 10
    for rule in re.findall(r"(QPushButton|QLineEdit)\s*\{([^}]*)\}", qss):
        pads = re.findall(r"(?<![-\w])padding\s*:\s*(\d+)px", rule[1])
        assert pads and all(int(p) >= S.SPACING["pad"] for p in pads)
