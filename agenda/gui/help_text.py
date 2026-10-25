"""Qt-free help texts: toolbar tooltips and section descriptions (plain text, no HTML)."""

from agenda.gui.bar_model import SECTION_LABELS

TOOLTIPS: dict[str, str] = {
    "open_config": (
        "Open a YAML configuration file. Its values are loaded into the settings panel "
        "and replace all current settings, and the preview is rebuilt."
    ),
    "save_config": (
        "Save the current settings as a YAML configuration file. "
        "The saved file can be loaded again later with Open."
    ),
    "export_pdf": (
        "Export the full agenda as a PDF file. The pages are rendered in a background "
        "thread while a progress bar is shown, so the window stays responsive. "
        "Folded booklets are imposed into printer sheets."
    ),
    "prev": (
        "Go to the previous page, spread or sheet. The step size depends on the current "
        "mode: one page in Single, one spread in Spread, one printer sheet in Sheet."
    ),
    "next": (
        "Go to the next page, spread or sheet. The step size depends on the current "
        "mode: one page in Single, one spread in Spread, one printer sheet in Sheet."
    ),
    "mode_single": (
        "Single mode: show one page at a time. Useful for checking the layout "
        "of an individual page."
    ),
    "mode_spread": (
        "Spread mode: show the left and right pages as they face each other when bound. "
        "This is the default, and the best way to check alternating margins."
    ),
    "mode_sheet": (
        "Sheet mode: show the imposed printer sheet, with the pages placed as they are "
        "printed. This only applies to folded booklets; otherwise there are no sheets."
    ),
    "zoom": (
        "Preview zoom. Choose fit to scale the pages to the available space, "
        "or a fixed percentage such as 100%."
    ),
}

EXPORT_DISABLED_REASON = (
    "Export is disabled because the current settings are invalid. "
    "Fix the highlighted settings to enable it."
)

SECTION_DESCRIPTIONS: dict[str, str] = {
    "front_back": (
        "front and back matter: cover, personal info, goals, yearly overview, "
        "notes, contacts and back cover."
    ),
    "monthly": "monthly overview pages, one per month.",
    "weekly": "weekly planner pages.",
    "daily": "daily planner pages, one per day.",
    "optional": "pages from the optional categories you enabled.",
    "value_added": "pages from the value-added categories you enabled.",
    "padding": (
        "blank filler pages inserted automatically so that booklets fill whole sheets. "
        "Shown hatched."
    ),
}


def section_tooltip(key: str) -> str:
    """"<Label>: <description>" for a section key; unknown keys fall back to the key."""
    label = SECTION_LABELS.get(key, key)
    desc = SECTION_DESCRIPTIONS.get(key)
    return f"{label}: {desc}" if desc else label
