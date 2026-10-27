"""CLI help and messages follow AGENDA_UI_LANG / the locale variables (separate process: typer
builds the help at import)."""

import os
import subprocess
import sys

from agenda import uitext
from agenda.uitext import en, es


def _help(**env: str) -> str:
    base = {
        k: v
        for k, v in os.environ.items()
        if k not in {"AGENDA_UI_LANG", "LC_ALL", "LC_MESSAGES", "LANG"}
    }
    res = subprocess.run(
        [sys.executable, "-m", "agenda", "--help"],
        env=base | env,
        capture_output=True,
        text=True,
        check=True,
    )
    return " ".join(res.stdout.replace("│", " ").split())


def test_help_spanish_from_agenda_ui_lang():
    out = _help(AGENDA_UI_LANG="es")
    assert es.MESSAGES["cli.help"] in out
    assert es.MESSAGES["cli.dry_run"] in out


def test_help_english():
    out = _help(AGENDA_UI_LANG="en")
    assert en.MESSAGES["cli.help"] in out
    assert en.MESSAGES["cli.dry_run"] in out
    assert es.MESSAGES["cli.help"] not in out


def test_help_spanish_from_lang():
    out = _help(LANG="es_ES.UTF-8")
    assert es.MESSAGES["cli.help"] in out
    assert es.MESSAGES["cli.dry_run"] in out


def test_messages_translate():
    uitext.set_language("es")
    assert uitext.tr("cli.wrote", path="x.pdf") == "escrito x.pdf"
    assert uitext.tr("cli.error", message="m") == "agenda-gen: m"
