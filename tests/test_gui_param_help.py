import pytest

from agenda.config import Config
from agenda.gui import settings_model as sm
from agenda.gui.help_text import PARAM_DETAILS, PARAM_SHORT, param_tooltip

NAMES = list(Config.model_fields)


def test_keys_match_config():
    assert set(PARAM_SHORT) == set(PARAM_DETAILS) == set(Config.model_fields)


@pytest.mark.parametrize("n", NAMES)
def test_text_shape(n):
    s, d = PARAM_SHORT[n], PARAM_DETAILS[n]
    assert s and len(s) <= 90 and "\n" not in s
    assert len(d) >= 60 and d.endswith(".") and d != s


@pytest.mark.parametrize(
    "spec",
    [s for s in sm.field_specs() if s.kind in (sm.CHOICE, sm.OPT_CHOICE, sm.MULTI_CHOICE)],
    ids=lambda s: s.name,
)
def test_choices_in_detail(spec):
    for c in spec.choices:
        assert c in PARAM_DETAILS[spec.name]


def test_rules_mentioned():
    assert "imposition" in PARAM_DETAILS["crop_marks"]
    assert "booklet_folded" in PARAM_DETAILS["imposition"]
    assert "crop_marks" in PARAM_DETAILS["bleed"]
    assert "pages" in PARAM_DETAILS["preset"]
    assert "auto" in PARAM_DETAILS["num_booklets"]
    for n in ("inner_margin", "outer_margin", "bleed", "creep_mm"):
        assert "mm" in PARAM_SHORT[n]


@pytest.mark.parametrize("n", NAMES)
def test_param_tooltip(n):
    assert param_tooltip(n) == PARAM_SHORT[n]
    assert param_tooltip(n, True) == PARAM_SHORT[n] + "\n" + PARAM_DETAILS[n]


def test_unknown():
    assert param_tooltip("nope") == "nope"
