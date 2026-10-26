# agenda-gen

Generates a printable agenda/planner as a PDF: yearly, monthly, weekly and daily planners plus
optional extras (budget, habits, goals, QR codes and more), laid out for home printing and
binding into folded booklets.

- Any year, Monday or Sunday week start, holidays for any country (default `CR`)
- Spanish or English
- Page sizes: `half_letter`, `a5`, `b6`, `letter`, `a4`, or custom `WxH` in mm
- Alternating inner/outer margins, so the binding side is always wider
- Folded or flat booklets, with automatic padding and filler pages
- Optional 2-up imposition with bleed and crop marks, ready for duplex printing
- A command line tool and a desktop GUI with live preview

## Install

Requires Python 3.11+.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -e .            # CLI only
pip install -e ".[gui]"     # CLI + GUI (PySide6, pypdfium2)
pip install -e ".[dev]"     # tests and linting
```

The Inter fonts are bundled in `assets/fonts/`.

## Quick start

```sh
agenda-gen                            # default agenda -> output/agenda.pdf
agenda-gen --config config.yaml       # use a settings file
agenda-gen --config config.yaml --dry-run   # print the page/booklet summary only
agenda-gen --list                     # show the page catalog
agenda-gui                            # open the GUI
```

`--dry-run` prints something like:

```
Pages: 540 (540 in booklets)
Booklets: 27 x 5 sheets (20 pages each)
Sheets: 135
Fillers: 41, padding: 10
```

## Configuration

Settings come from a YAML file (`--config`) and/or command-line flags; flags override the file.
Every key is optional, and unknown keys are errors. See [config.yaml](config.yaml) for an
annotated example.

```yaml
page_size: half_letter
year: 2027
week_start: monday
language: es
holiday_country: CR

booklet:
  size: 5          # units per booklet
  unit: sheets     # sheets | pages
  folded: true     # false = flat booklets

planners: [weekly, daily]
notes_pattern: dotted      # lined | dotted | grid | blank
pad_with: notes

pages: [cover, personal_info, yearly, monthly, weekly, habits, notes, contacts, back_cover]
```

Common flags:

| Flag | Purpose |
|---|---|
| `--page-size`, `--orientation` | Named size or `WxH` in mm; portrait or landscape |
| `--year`, `--week-start`, `--language`, `--holiday-country` | Calendar and locale |
| `--planners weekly,daily` | Which planners to include |
| `--daily-months "1-6,9"` | Limit daily pages to some months |
| `--pages a,b,c` / `--category core,optional` | Choose pages by id or category |
| `--preset essential\|complete\|premium` | Ready-made page selection (used when `pages` is empty) |
| `--booklet-size`, `--booklet-unit`, `--folded/--flat` | Booklet layout |
| `--pad-with`, `--separate-covers`, `--creep-mm` | Booklet padding, covers, creep |
| `--imposition`, `--crop-marks`, `--bleed` | Print-ready 2-up sheets |
| `--qr-url URL` | Content for the QR page (repeatable) |
| `--notes-pattern`, `--page-numbers` | Page details |
| `-o, --output` | Output PDF path (default `output/agenda.pdf`) |
| `--debug-grid` | Overlay margins, columns and baseline grid |

Run `agenda-gen --help` for the full list.

### Sections

The settings are grouped into sections, in the GUI and in the YAML file: **Global** (page size,
year, language, booklets, page list, `holidays_file`), **Notes & padding**, one section per page
template that has options (`daily`, `weekly`, `contacts`, `schedule`, `habits`, `qr`, and the niche
packs `niche_entrepreneur`, `niche_student`, `niche_fitness`) and **Colors & styling** (`style`).
Each section can be written as a block (`notes:`, `daily:`, `contacts:`, `schedule:`, `habits:`,
`qr:`, `niche_*:`, `style:`) with short keys. Save writes the blocks; flat keys (`notes_pages`,
`daily_hour_start`, ...) still load and give the same result.

```yaml
notes:      {pattern: dotted, pages: 1, pad_with: notes, extra_padding: 0}
daily:      {months: "1-12", hour_start: 6, hour_end: 21, holidays: true, quotes: false}
contacts:   {pages: 1}
schedule:   {first_hour: 7, last_hour: 21}
habits:     {max: 20}
qr:         {urls: ["https://example.com"]}
niche_student: {pages: 1}
style:      {theme: minimal}
holidays_file: examples/holidays.txt
```

Values that used to be fixed in the pages are now settings; the defaults reproduce the old output:

| Setting (flat key) | Default | Meaning |
|---|---|---|
| `daily_hour_start` / `daily_hour_end` | 6 / 21 | Hours listed on day pages (start < end) |
| `schedule_first_hour` / `schedule_last_hour` | 7 / 21 | Hours on the weekly schedule page |
| `habits_max` | 20 | Habit rows on the habit tracker |
| `notes_pages`, `contacts_pages` | 1 | Back-matter Notes / Contacts pages (0 removes them) |
| `niche_entrepreneur_pages`, `niche_student_pages`, `niche_fitness_pages` | 1 | Copies of each pack |

### Padding

A padding unit is one copy of the `pad_with` page (a catalog id, default `notes`), placed before
the back cover. `extra_padding` (default 0) is the minimum number of units; the count is rounded
up so the last booklet is whole, so you may get more than asked. `notes_pages` are separate,
regular back-matter pages and are not padding.

### Day extras

Day pages can show, besides the date:

- **Holiday names** (`daily_holidays`, on by default): in the header. Holidays come from the
  `holiday_country` library merged with `holidays_file` (lines `MM-DD name`), the same on every
  page that uses holidays.
- **A rotating phrase** (`daily_quotes`, off by default): in the footer, one per day of the year,
  cycling through the list (day 1 uses the first phrase). `daily_quotes_file` gives your own list,
  one phrase per line; otherwise the built-in phrases are used.
- **Extra data** (`daily_extra_file`): lines `MM-DD text` (every year) or `YYYY-MM-DD text` (that
  year only), shown right of the footer; several on one date are joined with " · ".

Files are UTF-8; blank lines and lines starting with `#` are ignored. See
[examples/](examples/). Paths are checked when the config is built and relative paths are resolved
against the current directory. Files are read once and cached by path and modification time. A file edited while the GUI is open
is re-read only when its timestamp changes; if the preview looks stale, touch the file or restart.

## Pages

`agenda-gen --list` prints the catalog with categories, value scores and presets:

- **core**: cover, personal info, yearly calendar, monthly, weekly (two-page spread), daily,
  notes, contacts, back cover
- **optional**: goals, important dates, to-do, projects, budget, habit tracker, monthly review,
  schedule, holidays, passwords
- **value_added**: quotes, vision board, health tracker, meals, gratitude, media log, travel,
  30-day challenges, idea map, QR codes, physical extras guide, entrepreneur/student/fitness packs

Pages are ordered front matter → per month (monthly, then each week's spread and its dailies) →
optional → value-added → back matter. Weekly spreads always start on a left page.

## Printing

With folded booklets (the default) each sheet holds 4 pages and is folded in half; page counts
are padded to a multiple of 4 using the `pad_with` page. `--imposition` writes 2-up sheets in
booklet order on landscape letter/A4, so you can print duplex, fold and stack. Add
`--crop-marks` and `--bleed` when trimming.

### Export

In the GUI, **Export PDF** opens a dialog with these options (the same ones the CLI takes):

| Option | CLI flag | Meaning |
| --- | --- | --- |
| Page numbers | `--page-numbers` / `--no-page-numbers` | Print a number on each page |
| First number | `--page-number-start N` | Number printed on the first numbered page |
| First numbered page | `--page-number-first N` | 1-based plan page that gets the first number (3 skips cover and inside cover) |
| Position | `--page-number-position outer\|center\|inner` | Outer = away from the binding |
| Placement | `--page-number-placement margin\|footer` | Bottom margin band, or inside the page footer band |
| Format | `--page-number-format "{n} / {total}"` | Must contain `{n}`; `{total}` is the last printed number |
| Layout: single pages | (default) | One PDF page per agenda page |
| Layout: spreads | `--spreads` | 2-up reader spreads in reading order |
| Layout: booklets | `--imposition --folded` | Saddle-stitch sheets, 2-up, in booklet order |
| Sheet size | `--sheet-size auto\|letter\|a4` | Sheet for spreads and booklets |
| Crop marks / bleed | `--crop-marks`, `--bleed MM` | Trim marks; need spreads or booklets |
| Booklet size, unit, count, covers | `--booklet-size`, `--booklet-unit`, `--num-booklets`, `--separate-covers` | Booklet structure |
| Page range | `--page-range "1-4,9"` | Export only these pages; single pages layout only (not with spreads or booklets) |
| Output | `--output FILE` | Target file |

Spreads and booklets are mutually exclusive. The page range is never saved to the config. The dialog
shows the equivalent `agenda-gen` command and disables Export while the combination is invalid. It
also has "open after export"; that choice and the last output folder are remembered between runs.

## GUI

`agenda-gui` shows a settings panel generated from the config model, a live preview (single,
spread or sheet view), a section bar showing where each section and booklet falls, and export
with a progress bar (Export PDF opens the export dialog described under Printing; the export
options no longer appear in the settings panel). Settings can be opened from and saved to YAML. See
[docs/architecture/gui.md](docs/architecture/gui.md).

The settings panel is a list of collapsible sections (Global starts open). Template sections have an
enable checkbox in the header: for `daily` and `weekly` it adds or removes the planner, for
`schedule`, `habits`, `qr` and the niche packs it adds or removes the page from `pages`, and for
`contacts` it sets the page count (0 = off, on = 1). The main preview follows the focused or expanded
section and shows that template's own sample page; Global shows the full agenda, and Colors & styling
keeps the last template. A disabled template is previewed grayed out. The appearance (dark by
default, or light) is set in Colors & styling and remembered between runs.

## Development

```sh
pytest
ruff check .
```

Project layout:

```
agenda/          core: config, calendar, page plan, drawing, imposition, CLI
agenda/pages/    page classes (core, optional, value_added)
agenda/gui/      PySide6 app
assets/fonts/    bundled Inter fonts
docs/            plan, architecture notes and decisions
tests/
```

Design notes live in [docs/architecture/](docs/architecture/) and
[docs/decisions/](docs/decisions/); progress is tracked in
[docs/plan/phases.md](docs/plan/phases.md).
