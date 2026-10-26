"""Notes/contacts page counts and extra padding (phase 12)."""

import pytest
from pydantic import ValidationError

from agenda import templates as T
from agenda.assembler import build_plan, pages_per_booklet, plan_booklets, summarize
from agenda.config import Config
from agenda.gui.settings_model import default_values
from agenda.pages.core import Contacts, Notes


def _per(cfg):
    return pages_per_booklet(cfg.booklet_size, cfg.booklet_unit, cfg.booklet_folded)


def _kinds(plan, kind):
    return [e for e in plan if e.kind == kind]


@pytest.mark.parametrize("year,pad", [(2026, 10), (2025, 12)])
def test_defaults_fingerprint(year, pad):
    plan = build_plan(Config(year=year))
    assert len(plan) == 540
    assert len(_kinds(plan, "padding")) == pad
    assert len(_kinds(plan, "filler")) == 41


def test_defaults_validation():
    c = Config()
    assert (c.notes_pages, c.contacts_pages, c.extra_padding) == (1, 1, 0)
    for bad in ({"notes_pages": 51}, {"contacts_pages": -1}, {"extra_padding": 201}):
        with pytest.raises(ValidationError):
            Config(**bad)


@pytest.mark.parametrize("extra", [0, 1, 5, 13])
def test_extra_padding_minimal_and_whole_booklets(extra):
    cfg = Config(year=2026, extra_padding=extra)
    plan = build_plan(cfg)
    n = len(_kinds(plan, "padding"))
    assert n >= extra
    assert plan_booklets(len(plan), _per(cfg), "auto").padding == 0
    if n > extra:  # one unit fewer must not complete the booklets
        fewer = build_plan(Config(year=2026, extra_padding=n - 1))
        assert len(_kinds(fewer, "padding")) == n or len(fewer) != len(plan)
    assert len(plan) % 4 == 0


def test_notes_and_contacts_counts():
    plan = build_plan(Config(year=2026, notes_pages=3))
    assert sum(1 for e in plan if e.page_class is Notes and e.kind == "page") == 3
    plan = build_plan(Config(year=2026, notes_pages=0, contacts_pages=0))
    assert not [e for e in plan if e.page_class in (Notes, Contacts) and e.kind == "page"]
    cfg = Config(year=2026, notes_pages=0, contacts_pages=0)
    assert plan_booklets(len(plan), _per(cfg), "auto").padding == 0


def test_pad_with_class():
    plan = build_plan(Config(year=2026, extra_padding=3, pad_with="notes"))
    pads = [e for e in _kinds(plan, "padding") if e.page_class is not None]
    assert pads and all(e.page_class is Notes for e in pads)
    plan = build_plan(Config(year=2026, extra_padding=3, pad_with="contacts"))
    pads = [e for e in _kinds(plan, "padding") if e.page_class is not None]
    assert pads and all(e.page_class is Contacts for e in pads)


def test_fixed_num_booklets_overflow():
    cfg = Config(year=2026, num_booklets=1, extra_padding=4)
    plan = build_plan(cfg)
    assert len(_kinds(plan, "padding")) >= 4
    assert summarize(plan, cfg).overflow > 0


def test_contacts_enable():
    assert not T.is_enabled(Config(contacts_pages=0), "contacts")
    assert T.is_enabled(Config(), "contacts")
    v = default_values()
    assert T.with_enabled({**v, "contacts_pages": 0}, "contacts", True)["contacts_pages"] == 1
    assert T.with_enabled({**v, "contacts_pages": 4}, "contacts", True)["contacts_pages"] == 4
    assert T.with_enabled(v, "contacts", False)["contacts_pages"] == 0
    assert T.has_enable_box("notes")
    assert T.group_of("extra_padding") == T.group_of("pad_with") == T.PADDING
    assert T.group_of("notes_pages") == "notes"
    assert T.group_of("contacts_pages") == "contacts"
