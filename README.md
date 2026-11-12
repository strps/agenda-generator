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

## Windows

### Ready-made program (no Python needed)

The GUI is built as a single `AgendaGenerator.exe` by GitHub Actions
([.github/workflows/windows-exe.yml](.github/workflows/windows-exe.yml)).

1. On GitHub, open **Actions > Windows executable**. Pick the latest successful run, or click
   **Run workflow** to build one from the current branch. Pushing a tag such as `v1.0` also starts a
   build.
2. When the run finishes, download the **AgendaGenerator-windows** artifact at the bottom of the run
   page. You must be signed in to GitHub, and artifacts expire after 90 days.
3. Unzip it and double-click `AgendaGenerator.exe`. There is nothing to install.

The program is not signed, so Windows SmartScreen may say "Windows protected your PC". Click
**More info > Run anyway**. The first start takes a few seconds, because the program unpacks itself.

Choose files with the **Browse...** buttons instead of typing paths. A relative path is resolved
against the folder the program was started from, which may not be the folder you expect.

### From source

1. Install Python 3.11 or newer from [python.org](https://www.python.org/downloads/windows/). In the
   installer, check **Add python.exe to PATH**.
2. In PowerShell, from the project folder:

   ```powershell
   py -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -e ".[gui]"
   agenda-gui                  # or agenda-gen for the command line
   ```

   If PowerShell refuses to run `Activate.ps1`, allow local scripts once with
   `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use `.venv\Scripts\activate.bat` in
   Command Prompt instead.

### Build the .exe yourself

With the virtual environment active:

```powershell
pip install ".[gui]" pyinstaller
pyinstaller --noconfirm packaging/agenda-gui.spec
```

The program is written to `dist\AgendaGenerator.exe`. The spec is
[packaging/agenda-gui.spec](packaging/agenda-gui.spec).

`AgendaGenerator.exe --self-test` checks the built program without opening the window: holiday
names (which need the bundled translations), a full export with the bundled fonts, the preview
renderer and the GUI icons. It writes the result to `self-test.log` in the current folder and exits
with code 0 (pass) or 1 (fail). The GitHub build runs it on every exe, so a file left out of the
bundle fails the build instead of the program on your computer.

### Holiday, phrase and note files in Excel

Make the sheet with the columns described under [Day extras](#day-extras), then use **File > Save
As** and pick **CSV UTF-8 (Comma delimited) (\*.csv)**, so accented letters are kept. Plain **CSV
(Comma delimited)** also works, including the `;`-separated files that Excel writes on Spanish
systems.

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
year, language, booklets, page list, `holidays_file`), **Padding** (`pad_with`, `extra_padding`),
one section per page template that has options (`daily`, `weekly`, `notes`, `contacts`, `schedule`,
`habits`, `qr`, and the niche packs `niche_entrepreneur`, `niche_student`, `niche_fitness`) and
**PDF colors & fonts** (`style`). The pad page itself is set up in its own section (e.g. the Notes
pattern). Older files with `pad_with`/`extra_padding` in the `notes:` block still load.
Per-month pages (`budget`, `habits`, `monthly_review`, `health`, `quotes`) listed in
`month_start`/`month_end` are printed inside every month instead of after the planner.
Each section can be written as a block (`padding:`, `month_start:`, `month_end:`, `notes:`, `daily:`, `weekly:`, `contacts:`, `schedule:`, `habits:`,
`qr:`, `niche_*:`, `style:`) with short keys. Save writes the blocks; flat keys (`notes_pages`,
`daily_hour_start`, ...) still load and give the same result.

```yaml
padding:    {pad_with: notes, extra_padding: 0}
notes:      {pattern: dotted, pages: 1}
daily:      {months: "1-12", hour_start: 6, hour_end: 21, holidays: true, quotes: false, filler: blank}
weekly:     {filler: blank}
month_start: {pages: [budget, habits]}    # printed right after each monthly page
month_end:  {pages: [monthly_review]}     # printed after each month's last week
contacts:   {pages: 1}
schedule:   {first_hour: 7, last_hour: 21}
habits:     {max: 20}
qr:         {urls: ["https://example.com"]}
niche_student: {pages: 1}
style:                     # all keys optional; omitted = theme / built-in defaults
  theme: minimal           # minimal | mono | ocean | forest | blush | lavender | peony
  accent: "#1e6fd9"        # ink, muted, line, accent, tint, weekend_fill, holiday_fill
  primary_font: inter      # inter or a .ttf/.otf path (headings, bold text)
  secondary_font: inter    # body text, labels, numbers
  title_padding: 2         # mm of fill on each side of a title background
holidays_file: examples/holidays.csv
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

### Fillers

Week spreads start on a left page. When a spread would start on a right page, a filler page is
put before it. `daily_filler` (`daily: {filler: ...}`) sets the filler that follows a week's day
pages, and `weekly_filler` (`weekly: {filler: ...}`) sets every other one, for example after a
monthly page or when there are no day pages. Each takes one of these values:

| Value | Effect |
|---|---|
| `blank` (default) | An empty page |
| `none` | No filler: the spread starts on a right page and is split across two leaves |
| a page id, e.g. `notes`, `todo` | That single-page template is printed in the slot |

CLI: `--weekly-filler`, `--daily-filler`. Fillers are not padding: padding only completes the
last booklet (see above).

### Day extras

Day pages can show, besides the date:

- **Holiday names** (`daily_holidays`, on by default): in the header. Holidays come from the
  `holiday_country` library merged with `holidays_file`, the same on every page that uses holidays.
- **A rotating phrase** (`daily_quotes`, off by default): in the footer, one per day of the year,
  cycling through the list (day 1 uses the first phrase). `daily_quotes_file` gives your own list;
  otherwise the built-in phrases are used.
- **Extra data** (`daily_extra_file`): shown right of the footer; several on one date are joined
  with " · ".

The three files are CSV, so you can make them in any spreadsheet (Excel, LibreOffice, Google
Sheets) and save or export as `.csv`. A header row is optional.

| File | Columns |
|---|---|
| `holidays_file` | `month`, `day`, `name`, `year` (optional: empty = every year) |
| `daily_extra_file` | `month`, `day`, `text`, `year` (optional: empty = every year) |
| `daily_quotes_file` | one phrase per row, first column |

The delimiter (`,`, `;` or tab) is detected, so CSVs saved with a Spanish or European locale work
too. Encoding is UTF-8 (with or without BOM), else Windows-1252. Empty rows and rows whose first
cell starts with `#` are ignored. Files that do not end in `.csv` are still read in the old text
format (one entry per line, `MM-DD text`). See [examples/](examples/). In the GUI each file has a
**Browse...** button. Paths are checked when the config is built and relative paths are resolved
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

### PDF style

The generated PDF's colors and fonts come from a theme plus optional overrides, all in the `style:`
block (flat Config names also load), with a CLI flag each. They apply to the export and the previews.

| YAML key (`style:`) | Config field | CLI flag | Meaning |
| --- | --- | --- | --- |
| `theme` | `theme` | `--theme` | Palette: `minimal` (default look), `mono`, `ocean`, `forest`, and the feminine `blush`, `lavender`, `peony`; unknown names render as minimal and the CLI warns |
| `ink` | `color_ink` | `--color-ink` | Text and strong lines |
| `muted` | `color_muted` | `--color-muted` | Secondary text |
| `line` | `color_line` | `--color-line` | Rules and dots |
| `accent` | `color_accent` | `--color-accent` | Month titles, highlights |
| `tint` | `color_tint` | `--color-tint` | Light fills |
| `weekend_fill` | `color_weekend_fill` | `--color-weekend-fill` | Weekend cells |
| `holiday_fill` | `color_holiday_fill` | `--color-holiday-fill` | Holiday cells |
| `primary_font` | `font_primary` | `--font-primary` | Headings, titles and bold text |
| `secondary_font` | `font_secondary` | `--font-secondary` | Body text, labels, numbers |
| `title_padding` | `title_padding` | `--title-padding` | Mm the weekend/holiday fill behind a day page header or week day row extends past the text on each side (default 2; 0 = flush) |

Colors are `#rgb` or `#rrggbb` (the `#` is optional); empty means the theme's color. A font is the
built-in `inter` or a path to a `.ttf`/`.otf` file (relative paths resolve against the working
directory). For a font such as `MyFont-Regular.ttf` the bold and italic styles are looked up as
`MyFont-Bold.ttf`, `MyFont-Italic.ttf` and `MyFont-BoldItalic.ttf`; a missing style falls back to the
regular file. The font must contain the glyphs of the agenda language. Make sure you are licensed to
embed any user font in a PDF you share.

In the GUI these are edited in the **PDF colors & fonts** section: a theme combo, color fields with a
swatch (opens a color dialog) and a clear button, and font fields with a Browse button.

## GUI

`agenda-gui` shows a settings panel generated from the config model, a live preview (single,
spread or sheet view), a section bar showing where each section and booklet falls, and export
with a progress bar (Export PDF opens the export dialog described under Printing; the export
options no longer appear in the settings panel). Settings can be opened from and saved to YAML. See
[docs/architecture/gui.md](docs/architecture/gui.md).

The settings panel groups its sections under flat collapsible headers: **General** (Global and PDF
colors & fonts), **Planner pages**, **Optional pages** and **Value-added pages** (the last two start
closed). Global starts open; a section with no settings of its own is a plain header that does not
collapse. Template sections have an enable checkbox in the
header: for `daily` and `weekly` it adds or removes the planner, for every optional and value-added
page (one section each) it adds or removes the page from `pages`, and for `contacts` it sets the page
count (0 = off, on = 1); `planners` and `pages` are not edited in Global. The main preview follows the
active section (focused, clicked or expanded, shown with an accent ring) and shows that template's own
sample page; Global shows the full agenda, and PDF colors & fonts keeps the last template. A disabled
template is previewed grayed out.

The look of the app itself (dark, light or system) is set in **Settings > Preferences...**
(`GuiSettingsDialog`), is remembered between runs in the GUI's own settings and never affects the
PDF. The panel section **PDF colors & fonts** edits the generated file's style instead (see PDF style).

The language of the app itself (GUI and CLI help and messages; English or Spanish) is separate from
the PDF `language` field, which only sets the language of the printed agenda. In the GUI, pick
**Settings > Preferences... > Language** (System, English, Español); it is saved between runs and
applies after a restart. Precedence: saved GUI preference, then `AGENDA_UI_LANG` (`en` or `es`), then
the system locale (`LC_ALL`, `LC_MESSAGES`, `LANG`; `es*` gives Spanish), then English. The CLI has no
flag: set `AGENDA_UI_LANG=es agenda-gen --help`, or rely on the locale. Config and file errors stay
in English.

## Development

```sh
pytest                # everything
pytest -m "not gui"   # Qt-free core only (tests needing PySide6 are marked `gui`)
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

### Adding a Config field

Give the field in `agenda/config.py` a `description` (short help), `json_schema_extra["detail"]`
(tooltip text) and `json_schema_extra["cli"]` (flags/type/csv/skip). The CLI option and the GUI
tooltips are generated from these (`agenda/fields.py`). Also add the field to
`agenda/templates.py` `SECTIONS`, and to the `settings_model` kind only if it is special.
