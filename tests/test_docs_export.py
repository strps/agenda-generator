"""The docs mention every export option added with the export dialog."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FLAGS = [
    "--page-number-start", "--page-number-first", "--page-number-position",
    "--page-number-placement", "--page-number-format", "--spreads", "--sheet-size",
    "--page-range",
]


def test_readme_lists_export_flags():
    text = (ROOT / "README.md").read_text()
    for flag in FLAGS:
        assert flag in text, flag


def test_gui_doc_mentions_export_dialog():
    text = (ROOT / "docs/architecture/gui.md").read_text()
    for word in ("ExportDialog", "export_model", "export/open_after", "export/last_dir"):
        assert word in text, word
