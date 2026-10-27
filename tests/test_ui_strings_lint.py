"""Lint: GUI text must reach Qt widgets through the UI catalog ``tr()``, never as literals.

AST only (no PySide6 import). A literal or f-string with a letter passed to a Qt text sink is a
violation; ``tr("key")`` calls, variables and empty strings are fine.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

GUI_DIR = Path(__file__).resolve().parent.parent / "agenda" / "gui"

# Files not converted yet (emptied by the last extraction phase).
PENDING: frozenset[str] = frozenset(
    {
        "settings_panel.py",
        "preview.py",
        "legend.py",
        "collapsible.py",
        "style_editors.py",
        "hover_tooltip.py",
        "section_bar.py",
    }
)

CONSTRUCTORS = {
    "QLabel",
    "QPushButton",
    "QCheckBox",
    "QRadioButton",
    "QGroupBox",
    "QAction",
    "QMenu",
    "ExpandingToolTip",
}
METHODS = {
    "setText",
    "setToolTip",
    "setStatusTip",
    "setWhatsThis",
    "setWindowTitle",
    "setPlaceholderText",
    "setTitle",
    "addMenu",
    "showMessage",
}
FIRST_ARG_METHODS = {"addItem", "addItems"}  # later args are item data, not text


def _has_letter_text(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and any(c.isalpha() for c in node.value)
    if isinstance(node, ast.JoinedStr):
        return any(
            isinstance(p, ast.Constant) and any(c.isalpha() for c in str(p.value))
            for p in node.values
        )
    return False


def _sink_args(call: ast.Call) -> list[ast.AST]:
    """Arguments of ``call`` that carry user-visible text, or [] when it is not a sink."""
    f = call.func
    all_args = [*call.args, *(k.value for k in call.keywords)]
    if isinstance(f, ast.Name) and f.id in CONSTRUCTORS:
        return all_args
    if isinstance(f, ast.Attribute):
        if f.attr in METHODS:
            return all_args
        if f.attr in FIRST_ARG_METHODS:
            return call.args[:1]
        if isinstance(f.value, ast.Name) and f.value.id == "QMessageBox":
            return all_args
    return []


def violations(source: str) -> list[tuple[int, str]]:
    found = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call):
            for arg in _sink_args(node):
                if _has_letter_text(arg):
                    found.append((arg.lineno, ast.unparse(arg)))
    return sorted(found)


def _gui_files() -> list[Path]:
    return sorted(GUI_DIR.glob("*.py"))


def test_pending_names_exist():
    names = {p.name for p in _gui_files()}
    assert PENDING <= names


@pytest.mark.parametrize("path", _gui_files(), ids=lambda p: p.name)
def test_gui_file_has_no_literal_text(path: Path):
    if path.name in PENDING:
        pytest.skip("not converted to the UI catalog yet")
    assert violations(path.read_text(encoding="utf-8")) == []


def test_converted_files_are_not_pending():
    assert not PENDING & {"app.py", "prefs_dialog.py", "export_dialog.py"}


def test_lint_flags_literals():
    assert violations('QLabel("Hello")')
    assert violations('x.setToolTip(f"Go {n}")')
    assert violations('QMessageBox.warning(self, "Title", err)')
    assert violations('box.addItem("Dark", "dark")')


def test_lint_accepts_catalog_and_non_text():
    assert not violations('QLabel(tr("k"))')
    assert not violations('QLabel("")')
    assert not violations('w.setObjectName("save_button")')
    assert not violations('box.addItem(tr("k"), "dark")')
    assert not violations("x.setToolTip(f\"{tr('k')}\")")
    assert not violations("x.setText(msg)")
