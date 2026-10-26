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
    "appearance": (
        "Application look: dark, light, or system (follow the desktop theme). "
        "The choice is saved between runs."
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


# Short (one phrase) and detailed texts for every Config field, keyed by field name.
PARAM_SHORT: dict[str, str] = {
    "page_size": "Page size: a name or custom WxH in mm.",
    "orientation": "Page orientation.",
    "inner_margin": "Margin on the binding side, in mm.",
    "outer_margin": "Margin on the outer edges, in mm.",
    "bleed": "Gap before each crop mark, in mm.",
    "booklet_size": "Size of one booklet, in sheets or pages.",
    "booklet_unit": "Unit of the booklet size.",
    "booklet_folded": "Folded (4 pages per sheet) or flat booklets.",
    "num_booklets": "Number of booklets, or auto.",
    "pad_with": "Page id used to fill the last booklet.",
    "separate_covers": "Keep the covers apart from the booklets.",
    "creep_mm": "Creep compensation for folded sheets, in mm.",
    "planners": "Which planner pages to include.",
    "daily_months": "Months that get daily pages.",
    "pages": "Catalog pages to include.",
    "preset": "Page selection by value score.",
    "notes_pattern": "Pattern of the notes pages.",
    "page_numbers": "Print page numbers on the pages.",
    "page_number_start": "Number printed on the first numbered page.",
    "page_number_first": "Plan page that gets the first number.",
    "page_number_position": "Where the number sits: outer, center or inner.",
    "page_number_placement": "Number in the bottom margin or in the page footer.",
    "page_number_format": "Label text; {n} is the number, {total} the last one.",
    "qr_urls": "Texts or URLs for the QR page, one per line.",
    "daily_hour_start": "First hour printed on day pages (0-23).",
    "daily_hour_end": "Last hour printed on day pages (0-23).",
    "schedule_first_hour": "First hour of the weekly schedule (0-23).",
    "schedule_last_hour": "Last hour of the weekly schedule (0-23).",
    "habits_max": "Maximum habit rows per month (1-40).",
    "niche_entrepreneur_pages": "Number of Entrepreneur pack pages (1-20).",
    "niche_student_pages": "Number of Student pack pages (1-20).",
    "niche_fitness_pages": "Number of Fitness pack pages (1-20).",
    "notes_pages": "Number of back-matter Notes pages (0-50).",
    "contacts_pages": "Number of back-matter Contacts pages (0-50).",
    "extra_padding": "Minimum number of padding pages to add (0-200).",
    "daily_holidays": "Print the holiday name on day pages.",
    "daily_quotes": "Print a rotating phrase on day pages.",
    "daily_quotes_file": "Text file with one phrase per line.",
    "daily_extra_file": "File of dated notes shown on day pages.",
    "year": "Calendar year of the agenda.",
    "week_start": "First day of the week.",
    "language": "Language of the printed texts.",
    "holiday_country": "Country code used for holidays, e.g. CR.",
    "holidays_file": "Extra holidays file, merged with the library.",
    "theme": "Color palette and typography.",
    "imposition": "Export in booklet print order.",
    "crop_marks": "Draw crop marks on the imposed sheets.",
    "output": "Path of the exported PDF.",
    "debug_grid": "Overlay margins, columns and baseline.",
}

PARAM_DETAILS: dict[str, str] = {
    "page_size": (
        "Size of the finished page. Use a known name (half_letter, a5, letter, a4, b6) or a "
        "custom size written as WxH in millimetres. Orientation is applied on top of it."
    ),
    "orientation": (
        "Whether the page is taller than wide (portrait) or wider than tall (landscape). "
        "It swaps the width and height of the page size for every page."
    ),
    "inner_margin": (
        "Free space, in mm, on the side of the page where the booklet is bound. "
        "A larger value moves the content away from the fold and shrinks the content width."
    ),
    "outer_margin": (
        "Free space, in mm, on the outer edges of the page, away from the binding. "
        "A larger value shrinks the area available for the content."
    ),
    "bleed": (
        "Gap, in mm, left between the page and each crop mark. It only has an effect when "
        "crop_marks is on, which in turn needs imposition."
    ),
    "booklet_size": (
        "How big one booklet is. It is counted in sheets or in pages depending on "
        "booklet_unit (sheets or pages). With pages it must be a multiple of 4 for folded "
        "booklets and of 2 for flat ones."
    ),
    "booklet_unit": (
        "Whether booklet_size counts sheets or pages. A folded sheet holds 4 pages and a "
        "flat double-sided sheet holds 2, so 5 sheets are 20 folded pages."
    ),
    "booklet_folded": (
        "On: saddle-stitched booklets with 4 pages per sheet. Off: flat double-sided sheets "
        "with 2 pages per sheet. Imposition requires folded booklets."
    ),
    "num_booklets": (
        "How many booklets the agenda is split into. Use auto to derive the number from the "
        "content, or a whole number of at least 1. The last booklet is filled with pad_with."
    ),
    "pad_with": (
        "Catalog page id repeated to fill the last booklet so that it ends on a whole sheet. "
        "These filler pages show as padding in the section bar. The default is notes."
    ),
    "separate_covers": (
        "When on, the cover and back cover are excluded from the booklet count, so padding "
        "goes before the back cover and the covers can be printed separately on card stock."
    ),
    "creep_mm": (
        "Shift, in mm, applied to the inner pages of folded sheets on the imposed output to "
        "compensate for paper thickness. It is negligible for small booklets and 0 disables it."
    ),
    "planners": (
        "Which planner page types are generated: weekly, daily or both. Daily pages are "
        "limited to the months in daily_months, which also limits the page count."
    ),
    "daily_months": (
        "Months (1-12) that get daily pages, for example 1-6,9. Fewer months give fewer pages "
        "and a thinner agenda. It only matters when the daily planner is selected."
    ),
    "pages": (
        "Explicit list of catalog page ids to include. When set, it always overrides the "
        "preset. When empty and no preset is chosen, all core pages are used."
    ),
    "preset": (
        "Selects pages by value score: essential, complete or premium. It is only used when "
        "pages is empty, because explicit pages always win over the preset."
    ),
    "notes_pattern": (
        "Ruling printed on the notes pages: lined, dotted, grid or blank. "
        "It also applies to notes pages added as booklet padding."
    ),
    "page_numbers": (
        "When on, a page number is printed on each page. When off, the pages carry "
        "no numbers. Start, first page, position, placement and format refine it "
        "(page_number_start, page_number_first, page_number_position, "
        "page_number_placement, page_number_format)."
    ),
    "page_number_start": (
        "Number printed on the first numbered page (0-9999, default 1). "
        "Only used when page_numbers is on."
    ),
    "page_number_first": (
        "1-based plan page that gets the first number (default 1). Earlier pages are "
        "unnumbered, e.g. 3 skips the cover and inside cover. Only used when page_numbers is on."
    ),
    "page_number_position": (
        "Horizontal position: outer (away from the binding, default), center or inner "
        "(next to the binding). Only used when page_numbers is on."
    ),
    "page_number_placement": (
        "margin (default) prints the number in the bottom margin below the page content; "
        "footer prints it inside the page footer band. Only used when page_numbers is on."
    ),
    "page_number_format": (
        "Label text, 1-24 characters. {n} is the page number (required) and {total} the "
        "last number, e.g. '{n} / {total}'. Only used when page_numbers is on."
    ),
    "qr_urls": (
        "Texts or URLs for the qr page, one QR code each, entered one per line. At most 24 "
        "entries of at most 200 characters, and empty lines are not allowed."
    ),
    "daily_hour_start": (
        "First hour of the hourly schedule on day pages, 0-23 (default 6, shown as 06:00). It "
        "must be less than daily_hour_end. The page still shows fewer hours when they do not fit."
    ),
    "daily_hour_end": (
        "Last hour of the hourly schedule on day pages, 0-23 (default 21, shown as 21:00). It "
        "must be greater than daily_hour_start. The page still shows fewer hours when they do not fit."
    ),
    "schedule_first_hour": (
        "Hour of the first row of the weekly schedule page, 0-23 (default 7). It must be less "
        "than schedule_last_hour. The page still shows fewer rows when they do not fit."
    ),
    "schedule_last_hour": (
        "Hour of the last row of the weekly schedule page, 0-23 (default 21), which caps the "
        "number of hours. It must be greater than schedule_first_hour. The page still shows "
        "fewer rows when they do not fit."
    ),
    "habits_max": (
        "Maximum number of habit rows on each monthly habit tracker page, 1-40 (default 20). "
        "The page still shows fewer rows when they do not fit."
    ),
    "niche_entrepreneur_pages": (
        "How many copies of the Entrepreneur pack page are printed, 1-20 (default 1). "
        "It only applies when niche_entrepreneur is in pages."
    ),
    "niche_student_pages": (
        "How many copies of the Student pack page are printed, 1-20 (default 1). "
        "It only applies when niche_student is in pages."
    ),
    "niche_fitness_pages": (
        "How many copies of the Fitness pack page are printed, 1-20 (default 1). "
        "It only applies when niche_fitness is in pages."
    ),
    "notes_pages": (
        "How many Notes pages are printed in the back matter, 0-50 (default 1). 0 removes "
        "them. Padding made with pad_with=notes is separate and is set by extra_padding."
    ),
    "contacts_pages": (
        "How many Contacts pages are printed in the back matter, 0-50 (default 1). 0 removes "
        "them and the Contacts section is then off."
    ),
    "extra_padding": (
        "Minimum number of padding units (copies of the pad_with page, or blank pages) put "
        "before the back cover, 0-200 (default 0). The agenda may get more padding than "
        "asked, to complete the last booklet, so booklets stay whole."
    ),
    "daily_holidays": (
        "When on (the default), the day pages print the name of the day's holiday in the "
        "header, before the week number. It uses the same holidays as the calendar pages, "
        "including those from holidays_file."
    ),
    "daily_quotes": (
        "When on, the footer of each day page shows an inspirational phrase. Phrases rotate: "
        "one per day of the year, cycling through the list. Off by default."
    ),
    "daily_quotes_file": (
        "Optional text file with one phrase per line (UTF-8; blank lines and lines starting "
        "with # are ignored). The phrases rotate, one per day of the year, cycling. Empty "
        "means the built-in phrases of the chosen language. Used only with daily_quotes."
    ),
    "daily_extra_file": (
        "Optional text file with one dated entry per line, as 'MM-DD text' (every year) or "
        "'YYYY-MM-DD text' (that year only); lines starting with # are comments. The text is "
        "shown in the footer of the matching day page. Several entries on one date are joined."
    ),
    "year": (
        "Year of the calendar (1900-2200). It sets all dates, weekdays and holidays "
        "on the monthly, weekly and daily pages."
    ),
    "week_start": (
        "First day of the week, monday or sunday. It changes the column order of the "
        "monthly grids and where each weekly page begins."
    ),
    "language": (
        "Language of month names, weekdays and other printed texts: es (Spanish) or "
        "en (English)."
    ),
    "holiday_country": (
        "ISO country code, for example CR, whose public holidays are marked on the calendar "
        "pages. It is converted to upper case."
    ),
    "holidays_file": (
        "Optional text file of your own holidays, one per line as 'MM-DD name' (every year) "
        "or 'YYYY-MM-DD name' (that year only); lines starting with # are comments. They are "
        "merged with the country holidays and shown the same way on every page."
    ),
    "theme": (
        "Name of the theme that sets the color palette and typography of the PDF. "
        "The default is minimal."
    ),
    "imposition": (
        "Export the pages in booklet print order, so the printed sheets can be folded into a "
        "booklet. It requires booklet_folded to be on."
    ),
    "crop_marks": (
        "Draw crop marks on the imposed sheets to show where to cut. It requires imposition "
        "to be on, and the bleed setting controls the gap before each mark."
    ),
    "output": (
        "File path of the exported PDF. The file is written there when you use Export "
        "and is overwritten if it exists."
    ),
    "debug_grid": (
        "Overlay the margins, columns and baseline grid on every page. Use it to check "
        "the layout, and turn it off for the final print."
    ),
}


def param_tooltip(name: str, expanded: bool = False) -> str:
    """Short text for a Config field, plus detail after a newline when expanded."""
    short = PARAM_SHORT.get(name)
    if short is None:
        return name
    detail = PARAM_DETAILS.get(name)
    return f"{short}\n{detail}" if expanded and detail else short
