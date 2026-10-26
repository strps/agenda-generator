import json
import subprocess
import sys
from pathlib import Path

import pytest

from agenda import fields
from agenda.config import Config
from agenda.gui import help_text

ROOT = Path(__file__).resolve().parent.parent
PIN = json.loads((ROOT / "tests" / "data" / "param_help.json").read_text(encoding="utf-8"))


def test_field_names_follow_config_order():
    assert fields.field_names() == list(Config.model_fields)


def test_every_field_has_help_and_cli():
    for n in fields.field_names():
        assert fields.short_help(n), n
        assert fields.detail_help(n), n
        assert isinstance(fields.cli_meta(n), dict), n


def test_param_dicts_match_pin():
    assert help_text.PARAM_SHORT == PIN["short"]
    assert help_text.PARAM_DETAILS == PIN["details"]


def test_texts_live_only_on_config():
    source = (ROOT / "agenda" / "gui" / "help_text.py").read_text(encoding="utf-8")
    for n in fields.field_names():
        assert fields.short_help(n) not in source, n
        assert fields.detail_help(n) not in source, n


def test_cli_meta_keys_known():
    for n in fields.field_names():
        assert set(fields.cli_meta(n)) <= {"flags", "type", "csv", "skip"}, n


@pytest.mark.parametrize(
    ("name", "flags"),
    [("page_size", ["--page-size", "--size"]), ("booklet_folded", ["--folded/--flat"])],
)
def test_special_flags(name, flags):
    assert fields.cli_meta(name)["flags"] == flags


def test_fields_is_qt_free():
    code = "import sys, agenda.fields; assert not any(m.startswith('PySide6') for m in sys.modules)"
    r = subprocess.run([sys.executable, "-c", code], cwd=ROOT, check=False)
    assert r.returncode == 0


def test_es_catalog_covers_every_field_section_and_group():
    from agenda import templates, uitext
    from agenda.uitext import es_fields

    es = {**es_fields.MESSAGES}
    for n in fields.field_names():
        assert es[f"field.{n}.short"], n
        assert es[f"field.{n}.label"], n
        if fields.detail_help(n):  # English source is read under the autouse "en" language
            assert es[f"field.{n}.detail"], n
    for s in templates.SECTIONS:
        assert es[f"section.{s.key}"], s.key
    for g in templates.GROUPS:
        assert es[f"group.{g.key}"], g.key
    assert not (set(es) - {k for k in es if k.split(".")[0] in ("field", "section", "group")})
    assert uitext.get_language() == "en"


def test_localized_accessors():
    from agenda import templates, uitext

    english = Config.model_fields["year"].description
    assert fields.short_help("year") == english
    assert fields.field_label("page_size") == "page size"
    assert templates.section_label("daily") == "Day pages"
    assert templates.group_label("planner") == "Planner pages"
    uitext.set_language("es")
    assert fields.short_help("year") != english
    assert fields.short_help("year") == uitext.lookup("field.year.short")
    assert fields.detail_help("year") == uitext.lookup("field.year.detail")
    assert fields.field_label("page_size") == "tamaño de página"
    assert templates.section_label("daily") == "Páginas diarias"
    assert templates.group_label("planner") == "Páginas de planificador"
    assert help_text.PARAM_SHORT["year"] == fields.short_help("year")
    assert list(help_text.PARAM_SHORT) == fields.field_names()
    assert fields.short_help("page_number_format").count("{n}") == 1
