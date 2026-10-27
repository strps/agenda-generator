"""English UI text (source of truth)."""

MESSAGES: dict[str, str] = {
    "common.ok": "OK",
    "common.cancel": "Cancel",
    "prefs.restart_note": "The language change applies the next time the application starts.",
    "tooltip.open_config": "Open a YAML configuration file. Its values are loaded into the settings "
    "panel and replace all current settings, and the preview is rebuilt.",
    "tooltip.save_config": "Save the current settings as a YAML configuration file. The saved file "
    "can be loaded again later with Open.",
    "tooltip.export_pdf": "Open the export dialog to choose page numbers, layout, booklets and page "
    "range, then write the PDF. The pages are rendered in a background thread "
    "while a progress bar is shown, so the window stays responsive.",
    "tooltip.prev": "Go to the previous page, spread or sheet. The step size depends on the current "
    "mode: one page in Single, one spread in Spread, one printer sheet in Sheet.",
    "tooltip.next": "Go to the next page, spread or sheet. The step size depends on the current mode: "
    "one page in Single, one spread in Spread, one printer sheet in Sheet.",
    "tooltip.mode_single": "Single mode: show one page at a time. Useful for checking the layout of "
    "an individual page.",
    "tooltip.mode_spread": "Spread mode: show the left and right pages as they face each other when "
    "bound. This is the default, and the best way to check alternating "
    "margins.",
    "tooltip.mode_sheet": "Sheet mode: show the imposed printer sheet, with the pages placed as they "
    "are printed. This only applies to folded booklets; otherwise there are no "
    "sheets.",
    "tooltip.appearance": "Application look: dark, light, or system (follow the desktop theme). The "
    "choice is saved between runs.",
    "tooltip.color_swatch": "Click to pick this color in a color dialog. Shows the color in effect.",
    "tooltip.color_clear": "Clear the override and use the theme's color again.",
    "tooltip.font_browse": "Choose a .ttf or .otf font file. Bold and italic files next to it are "
    "used too.",
    "tooltip.global_section": "Settings for the whole agenda: page size, margins, booklets, year, "
    "language, planners and page numbers.",
    "tooltip.padding_section": "Which page fills the last booklet so it ends on a whole sheet, and "
    "the minimum number of padding pages. The pad page itself is set up in "
    "its own section, which shows a padding badge and a ringed box.",
    "tooltip.month_start_section": "Pages printed right after each monthly page, one per month (e.g. "
    "that month's budget or habit tracker). A checked page is ringed "
    "in its own section and is no longer printed after the planner.",
    "tooltip.month_end_section": "Pages printed after each month's last week, one per month (e.g. "
    "that month's review). A checked page is ringed in its own section "
    "and is no longer printed after the planner. A page can be at the "
    "start or the end, not both.",
    "tooltip.styling_section": "Style of the generated PDF: theme, colors and fonts. The look of this "
    "application is under Settings > Preferences and never changes the "
    "PDF.",
    "tooltip.preferences": "GUI look; does not change the PDF.",
    "tooltip.zoom": "Preview zoom. Choose fit to scale the pages to the available space, or a fixed "
    "percentage such as 100%.",
    "export.help.page_range": "Export only some pages, e.g. 1-4,9. Leave empty or type all for every "
    "page.",
    "export.help.page_range_detail": "Pages are numbered by their position in the agenda, starting at "
    "1. A page range only works with the single pages layout (not "
    "spreads or booklets). Page numbers printed on the pages keep "
    "their full-agenda values. It is not saved in the settings file. "
    "CLI: --page-range.",
    "export.help.layout_pages": "One agenda page per PDF page, in order.",
    "export.help.layout_pages_detail": "The default layout. Required for a page range. Flat booklets "
    "keep their page order.",
    "export.help.layout_spreads": "Two pages side by side per sheet, in reading order (no folding).",
    "export.help.layout_spreads_detail": "Sets spreads on and imposition off. Page 1 is a right page. "
    "Sheet size and crop marks apply. CLI: --spreads.",
    "export.help.layout_booklets": "Folded booklets imposed for printing and stapling.",
    "export.help.layout_booklets_detail": "Sets imposition and folded booklets on and spreads off. "
    "Pages are reordered so the printed sheets fold into "
    "booklets. CLI: --imposition --folded.",
    "export.help.open_after": "Open the PDF with the default viewer once it is written.",
    "export.help.open_after_detail": "Only remembered in the GUI; the command line never opens the "
    "file.",
    "export.help.cli_preview": "The agenda-gen command that produces the same PDF as these choices.",
    "export.help.cli_preview_detail": "Only options that differ from the defaults are listed. "
    "Settings outside this dialog come from the configuration file "
    "(--config).",
    "export.help.browse_output": "Choose where the PDF is written.",
    "export.help.browse_output_detail": "Opens a save dialog; a .pdf suffix is added when missing.",
    "export.disabled_reason": "Export is disabled because the current settings are invalid. Fix the "
    "highlighted settings to enable it.",
    "section_desc.front_back": "front and back matter: cover, personal info, goals, yearly overview, "
    "notes, contacts and back cover.",
    "section_desc.monthly": "monthly overview pages, one per month.",
    "section_desc.weekly": "weekly planner pages.",
    "section_desc.daily": "daily planner pages, one per day.",
    "section_desc.optional": "pages from the optional categories you enabled.",
    "section_desc.value_added": "pages from the value-added categories you enabled.",
    "section_desc.padding": "blank filler pages inserted automatically so that booklets fill whole "
    "sheets. Shown hatched.",
    "bar.section.front_back": "Front/back",
    "bar.section.monthly": "Monthly",
    "bar.section.weekly": "Weekly",
    "bar.section.daily": "Daily",
    "bar.section.optional": "Optional",
    "bar.section.value_added": "Value-added",
    "bar.section.padding": "Padding",
    "app.title": "Agenda Generator",
    "legend.no_plan": "No agenda: fix the settings",
    "summary.page.one": "{n} page",
    "summary.page.other": "{n} pages",
    "summary.sheet.one": "{n} sheet",
    "summary.sheet.other": "{n} sheets",
    "summary.booklet.one": "{n} booklet",
    "summary.booklet.other": "{n} booklets",
    "summary.padding.one": "{n} padding page",
    "summary.padding.other": "{n} padding pages",
    "summary.warning.one": "{n} warning",
    "summary.warning.other": "{n} warnings",
    "preview.mode.single": "Page",
    "preview.mode.spread": "Spread",
    "preview.mode.sheet": "Sheet",
    "preview.label": "{mode} {span} of {total}",
    "export.group.page_numbers": "Page numbers",
    "export.group.layout": "Layout",
    "export.group.booklets": "Booklets",
    "export.group.output": "Output",
    "export.err.single_pages": "page range: a page range can only be exported as single pages",
    "export.err.page_range": "page range: {message}",
    "bar.page": "Page {n}",
    "bar.booklet_sheet": "Booklet {booklet}, sheet {sheet}",
    "bar.blank": "Blank",
    "bar.filler": "{name} (filler)",
    "bar.week": "Week {number} ({start}–{end})",
    "date.short": "{month} {day}",
    "date.weekday": "{weekday} {date}",
    "pad.short.pad_with": "padding",
    "pad.short.weekly_filler": "week filler",
    "pad.short.daily_filler": "day filler",
    "pad.short.month_start_pages": "month start",
    "pad.short.month_end_pages": "month end",
    "pad.use.pad_with": "pads the last booklet",
    "pad.use.weekly_filler": "fills the slot before a week spread",
    "pad.use.daily_filler": "fills the slot after a week's day pages",
    "pad.use.month_start_pages": "printed after each monthly page",
    "pad.use.month_end_pages": "printed after each month's last week",
    "pad.text": "{short}: {use} (set in {section}).",
    "filler.blank": "Blank: leave the slot empty.",
    "filler.none": "None: no filler; a week spread may start on a right page.",
    "page.text": "{name}: {category} page, {size}{repeat}{where}.",
    "page.category.core": "core",
    "page.category.optional": "optional",
    "page.category.value_added": "value-added",
    "page.size.spread": "2-page spread",
    "page.size.one": "{n} page",
    "page.size.many": "{n} pages",
    "page.per_month": ", one per month",
    "page.where": ", set up in its {section} section",
    "header.count": "The box sets {field} to 0 (off) or at least 1 (on).",
    "header.enable": "The box includes it in the agenda.",
    "header.month_hint": "Pick Start or End of each month to print it inside every month instead.",
    "header.ringed": "A ringed box means the page is printed there even when the box is off.",
    "header.month_note": "While placed in each month it is not repeated after the planner.",
    "date.month_abbr.1": "Jan",
    "date.month_abbr.2": "Feb",
    "date.month_abbr.3": "Mar",
    "date.month_abbr.4": "Apr",
    "date.month_abbr.5": "May",
    "date.month_abbr.6": "Jun",
    "date.month_abbr.7": "Jul",
    "date.month_abbr.8": "Aug",
    "date.month_abbr.9": "Sep",
    "date.month_abbr.10": "Oct",
    "date.month_abbr.11": "Nov",
    "date.month_abbr.12": "Dec",
    "date.month.1": "January",
    "date.month.2": "February",
    "date.month.3": "March",
    "date.month.4": "April",
    "date.month.5": "May",
    "date.month.6": "June",
    "date.month.7": "July",
    "date.month.8": "August",
    "date.month.9": "September",
    "date.month.10": "October",
    "date.month.11": "November",
    "date.month.12": "December",
    "date.day_abbr.0": "Mon",
    "date.day_abbr.1": "Tue",
    "date.day_abbr.2": "Wed",
    "date.day_abbr.3": "Thu",
    "date.day_abbr.4": "Fri",
    "date.day_abbr.5": "Sat",
    "date.day_abbr.6": "Sun",
}
