import importlib

import pytest

from agenda import __version__

MODULES = [
    "config",
    "cli",
    "configfile",
    "gui.settings_model",
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
