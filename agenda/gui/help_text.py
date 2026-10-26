"""Qt-free help texts: toolbar tooltips and section descriptions (plain text, no HTML)."""

from agenda.fields import detail_help, field_names, short_help
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
        "Open the export dialog to choose page numbers, layout, booklets and page range, "
        "then write the PDF. The pages are rendered in a background thread while a "
        "progress bar is shown, so the window stays responsive."
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
    "appearance": (
        "Application look: dark, light, or system (follow the desktop theme). "
        "The choice is saved between runs."
    ),
    "color_swatch": "Click to pick this color in a color dialog. Shows the color in effect.",
    "color_clear": "Clear the override and use the theme's color again.",
    "font_browse": "Choose a .ttf or .otf font file. Bold and italic files next to it are used too.",
    "global_section": (
        "Settings for the whole agenda: page size, margins, booklets, year, language, "
        "planners and page numbers."
    ),
    "padding_section": (
        "Which page fills the last booklet so it ends on a whole sheet, and the minimum "
        "number of padding pages. The pad page itself is set up in its own section, which "
        "shows a padding badge and a ringed box."
    ),
    "month_start_section": (
        "Pages printed right after each monthly page, one per month (e.g. that month's budget "
        "or habit tracker). A checked page is ringed in its own section and is no longer "
        "printed after the planner."
    ),
    "month_end_section": (
        "Pages printed after each month's last week, one per month (e.g. that month's review). "
        "A checked page is ringed in its own section and is no longer printed after the "
        "planner. A page can be at the start or the end, not both."
    ),
    "styling_section": (
        "Style of the generated PDF: theme, colors and fonts. The look of this application "
        "is under Settings > Preferences and never changes the PDF."
    ),
    "preferences": "GUI look; does not change the PDF.",
    "zoom": (
        "Preview zoom. Choose fit to scale the pages to the available space, "
        "or a fixed percentage such as 100%."
    ),
}

EXPORT_HELP: dict[str, str] = {
    "page_range": "Export only some pages, e.g. 1-4,9. Leave empty or type all for every page.",
    "page_range_detail": (
        "Pages are numbered by their position in the agenda, starting at 1. "
        "A page range only works with the single pages layout (not spreads or booklets). "
        "Page numbers printed on the pages keep their full-agenda values. "
        "It is not saved in the settings file. CLI: --page-range."
    ),
    "layout_pages": "One agenda page per PDF page, in order.",
    "layout_pages_detail": (
        "The default layout. Required for a page range. Flat booklets keep their page order."
    ),
    "layout_spreads": "Two pages side by side per sheet, in reading order (no folding).",
    "layout_spreads_detail": (
        "Sets spreads on and imposition off. Page 1 is a right page. Sheet size and crop marks "
        "apply. CLI: --spreads."
    ),
    "layout_booklets": "Folded booklets imposed for printing and stapling.",
    "layout_booklets_detail": (
        "Sets imposition and folded booklets on and spreads off. Pages are reordered so the "
        "printed sheets fold into booklets. CLI: --imposition --folded."
    ),
    "open_after": "Open the PDF with the default viewer once it is written.",
    "open_after_detail": "Only remembered in the GUI; the command line never opens the file.",
    "cli_preview": "The agenda-gen command that produces the same PDF as these choices.",
    "cli_preview_detail": (
        "Only options that differ from the defaults are listed. Settings outside this dialog "
        "come from the configuration file (--config)."
    ),
    "browse_output": "Choose where the PDF is written.",
    "browse_output_detail": "Opens a save dialog; a .pdf suffix is added when missing.",
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
    """ "<Label>: <description>" for a section key; unknown keys fall back to the key."""
    label = SECTION_LABELS.get(key, key)
    desc = SECTION_DESCRIPTIONS.get(key)
    return f"{label}: {desc}" if desc else label


# Short and detailed texts for every Config field live on the fields themselves (agenda.config).
PARAM_SHORT: dict[str, str] = {n: short_help(n) for n in field_names()}
PARAM_DETAILS: dict[str, str] = {n: detail_help(n) for n in field_names()}


def param_tooltip(name: str, expanded: bool = False) -> str:
    """Short text for a Config field, plus detail after a newline when expanded."""
    short = PARAM_SHORT.get(name)
    if short is None:
        return name
    detail = PARAM_DETAILS.get(name)
    return f"{short}\n{detail}" if expanded and detail else short
