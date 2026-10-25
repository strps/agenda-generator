import importlib

import pytest

from agenda import __version__

MODULES = [
    "config",
    "cli",
    "configfile",
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
]


def test_version():
    assert __version__


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    importlib.import_module(f"agenda.{name}")
