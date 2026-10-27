"""Qt-free GUI text tables follow the UI language (no PySide6)."""

import pytest

from agenda import uitext
from agenda.gui import bar_model, export_model, layout
from agenda.gui import help_text as HT
from agenda.uitext import en, es


def test_english_unchanged():
    uitext.set_language("en")
    assert HT.TOOLTIPS["open_config"].startswith("Open a YAML configuration file.")
    assert bar_model.SECTION_LABELS["monthly"] == "Monthly"
    assert [t for t, _ in export_model.EXPORT_FIELDS] == [
        "Page numbers",
        "Layout",
        "Booklets",
        "Output",
    ]
    assert HT.EXPORT_DISABLED_REASON.startswith("Export is disabled")
    assert layout.WindowLayout().title == "Agenda Generator"


def test_spanish_tables():
    uitext.set_language("es")
    m = es.MESSAGES
    assert HT.TOOLTIPS["open_config"] == m["tooltip.open_config"]
    assert HT.TOOLTIPS["open_config"] != en.MESSAGES["tooltip.open_config"]
    assert HT.EXPORT_DISABLED_REASON == m["export.disabled_reason"]
    assert bar_model.SECTION_LABELS["monthly"] == m["bar.section.monthly"] != "Monthly"
    titles = [t for t, _ in export_model.EXPORT_FIELDS]
    assert titles == [
        m[f"export.group.{k}"] for k in ("page_numbers", "layout", "booklets", "output")
    ]
    assert not set(titles) & {"Page numbers", "Layout", "Booklets", "Output"}
    assert layout.WindowLayout().title == m["app.title"]


def test_tables_keep_dict_api():
    assert set(HT.SECTION_DESCRIPTIONS) == set(bar_model.SECTION_LABELS)
    assert "prev" in HT.TOOLTIPS and len(HT.TOOLTIPS) > 10
    with pytest.raises(KeyError):
        HT.TOOLTIPS["nope"]
    with pytest.raises(AttributeError):
        HT.__getattr__("NOPE")
