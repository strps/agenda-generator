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

## GUI

`agenda-gui` shows a settings panel generated from the config model, a live preview (single,
spread or sheet view), a section bar showing where each section and booklet falls, and export
with a progress bar. Settings can be opened from and saved to YAML. See
[docs/architecture/gui.md](docs/architecture/gui.md).

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
