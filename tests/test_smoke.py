import importlib

import pytest

from agenda import __version__

MODULES = [
    "config",
    "cli",
    "configfile",
    "gui.settings_model",
    "gui.preview_model",
    "gui.legend_model",
    "gui.render_cache",
    "gui.bar_model",
    "gui.export_model",
    "gui.section_colors",
    "sizes",
    "catalog",
    "calendar",
    "grid",
    "tokens",
    "draw",
    "themes",
    "assembler",
    "imposition",
    "exporter",
    "i18n",
    "pages",
    "pages.base",
    "pages.core",
    "pages.optional",
    "pages.value_added",
    "gui",
    "gui.layout",
]


def test_version():
    assert __version__


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(f"agenda.{name}")
