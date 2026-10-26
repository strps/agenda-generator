"""The docs describe the PDF style options and the GUI Settings dialog."""

from pathlib import Path

from agenda import themes

ROOT = Path(__file__).resolve().parent.parent
FLAGS = [
    "--theme", "--color-ink", "--color-muted", "--color-line", "--color-accent",
    "--color-tint", "--color-weekend-fill", "--color-holiday-fill",
    "--font-primary", "--font-secondary",
]


def test_readme_lists_style_options():
    text = (ROOT / "README.md").read_text()
    for word in [*FLAGS, *themes.THEMES, "Preferences"]:
        assert word in text, word


def test_gui_doc_mentions_style_editors():
    text = (ROOT / "docs/architecture/gui.md").read_text()
    for word in ("GuiSettingsDialog", "ColorEdit", "FontEdit", 'QSettings key "appearance"'):
        assert word in text, word
