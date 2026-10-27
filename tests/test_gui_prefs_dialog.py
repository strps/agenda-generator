import warnings

import pytest

from agenda import configfile


@pytest.mark.parametrize(
    "text, clean",
    [
        ("year: 2026\nappearance: dark\n", "year: 2026\n"),
        ("style: {appearance: dark, theme: minimal}\n", "style: {theme: minimal}\n"),
    ],
)
def test_legacy_appearance_ignored_with_warning(tmp_path, text, clean):
    a, b = tmp_path / "a.yaml", tmp_path / "b.yaml"
    a.write_text(text)
    b.write_text(clean)
    with pytest.warns(UserWarning, match="appearance.*GUI Settings"):
        got = configfile.load_yaml(a)
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert configfile.load_yaml(b) == got


@pytest.mark.gui
def test_appearance_items_translated_value_kept():
    from PySide6.QtWidgets import QApplication

    from agenda import uitext
    from agenda.gui.prefs_dialog import GuiSettingsDialog

    QApplication.instance() or QApplication([])
    uitext.set_language("es")
    dlg = GuiSettingsDialog("light")
    assert dlg.appearance() == "light"
    assert dlg.appearance_box.currentText() == "claro"


@pytest.mark.gui
def test_ui_language_combo_values_and_unknown_falls_back():
    from PySide6.QtWidgets import QApplication

    from agenda.gui.prefs_dialog import GuiSettingsDialog

    QApplication.instance() or QApplication([])
    assert GuiSettingsDialog("dark", ui_language="es").ui_language() == "es"
    assert GuiSettingsDialog("dark", ui_language="fr").ui_language() == "system"
    assert GuiSettingsDialog("dark").ui_language() == "system"
    dlg = GuiSettingsDialog("dark", ui_language="en")
    assert dlg.language_box.toolTip() == "" or dlg.language_tooltip is not None
    assert not dlg.restart_note.isVisibleTo(dlg)
    dlg.language_box.setCurrentIndex(dlg.language_box.findData("es"))
    assert dlg.restart_note.isVisibleTo(dlg)
