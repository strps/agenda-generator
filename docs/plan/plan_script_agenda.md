# Development Plan: Printable Agenda Generator in Python

> Suggested changes are in [improvements.md](improvements.md).

## 1. Goal

A script that generates a **print-ready PDF** of an agenda (planner), where the user:

- Selects which pages to include (core, optional and value-added).
- Sets the page size (default **half letter**).
- Sets the **booklet** (signature) size as a variable parameter (default **5 folded sheets = 20 pages**).
- Optionally exports in **imposition** order for binding.

> **Decision:** booklets are **folded by default** (saddle-stitched signatures): 1 sheet folded in half = 4 pages, so 5 sheets = 20 pages per booklet. Folding is **selectable** (`--folded / --no-folded`); unfolded means 1 sheet printed double-sided = 2 pages. The size parameter accepts both units (`--unit sheets|pages`).
>
> **Decision:** the agenda includes **both weekly and daily** planners by default. Either can be turned off.
>
> **Decision:** pages are drawn directly to PDF with **fpdf2**. See [ADR 0001](../decisions/0001-pdf-rendering-fpdf2.md).

---

## 2. Configuration parameters

| Parameter | Description | Default |
|---|---|---|
| `page_size` | Name (`half_letter`, `a5`, `letter`, `a4`, `b6`) or custom `width x height` | `half_letter` (139.7 x 215.9 mm) |
| `orientation` | `portrait` / `landscape` | `portrait` |
| `booklet_size` | Amount per booklet | `5` |
| `booklet_unit` | `sheets` or `pages` | `sheets` (5 sheets = 20 pages) |
| `booklet_folded` | Folded/saddle-stitched (4 pages per sheet) or flat double-sided (2 pages per sheet) | `true` |
| `planners` | Any of `weekly`, `daily` | `weekly, daily` |
| `daily_months` | Months that get daily pages (limits page count) | `1-12` |
| `num_booklets` | Number of booklets in the agenda (or `auto` based on content) | `auto` |
| `pages` | List of selected pages (catalog IDs) | All core pages |
| `year` | Agenda year | Current year |
| `week_start` | `monday` / `sunday` | `monday` |
| `language` | `es` / `en` | `es` |
| `holiday_country` | ISO code for holidays | `CR` (Costa Rica; configurable) |
| `inner_margin` | Margin on the binding side | 15 mm |
| `outer_margin` | Outer margin | 10 mm |
| `notes_pattern` | `lined`, `dotted`, `grid`, `blank` | `dotted` |
| `theme` | Color palette and typography | `minimal` |
| `imposition` | Export in booklet print order | `false` |
| `crop_marks` | Crop marks and bleed | `false` |
| `output` | PDF path | `agenda.pdf` |

Everything is configurable via a **YAML file**, the **command line (CLI)** or the **GUI** (see [gui.md](../architecture/gui.md)).

---

## 3. Page catalog

Each page is a module with an **ID**, a category, the number of pages it takes, and whether it repeats.

### 3.1 Core

| ID | Page | Pages | Repetition |
|---|---|---|---|
| `cover` | Cover | 1 | 1 |
| `personal_info` | Personal information | 1 | 1 |
| `yearly` | Yearly calendar | 1-2 | 1 |
| `monthly` | Monthly planner | 1-2 | x12 |
| `weekly` | Weekly planner (WO2P – week on two pages) | 2 | x52 or x53 (ISO weeks of the year) |
| `daily` | Daily planner (combined with weekly) | 1 | x365 / x366 (or per `daily_months`) |

> **Page count with both planners:** about 106 weekly + 365 daily + ~30 other pages ≈ 500 pages, or ~125 folded sheets (25 booklets of 5 sheets). The summary reports this, and `daily_months` can reduce it.
| `notes` | Notes (per pattern) | 1 | Variable |
| `contacts` | Contact directory | 1 | Variable |
| `back_cover` | Back cover | 1 | 1 |

### 3.2 Optional

| ID | Page | Repetition |
|---|---|---|
| `goals` | Yearly goals | 1 |
| `important_dates` | Birthdays and anniversaries | 1 |
| `todo` | To-do list | Variable |
| `projects` | Project planner | Variable |
| `budget` | Monthly budget / expenses | x12 |
| `habits` | Habit tracker | x12 |
| `monthly_review` | Monthly review | x12 |
| `schedule` | Schedules (classes / shifts) | 1 |
| `holidays` | Holidays of the year | 1 |
| `passwords` | Passwords (with warning) | 1-2 |

### 3.3 Value-added

| ID | Page | Value |
|---|---|---|
| `quotes` | Motivational quote per month | 3 |
| `vision_board` | Vision board | 4 |
| `health` | Health tracker (water, sleep, mood) | 4 |
| `meals` | Meal and grocery planner | 4 |
| `gratitude` | Gratitude journal | 4 |
| `media_log` | Books, movies and series | 3 |
| `travel` | Travel planner | 4 |
| `challenges30` | 30-day challenges | 4 |
| `ideas` | Idea map | 3 |
| `qr` | QR codes linking to digital resources | 5 |
| `physical_extras` | Guide for stickers, dividers and pocket (printed separately) | 5 |
| `niche_*` | Niche pages (entrepreneur, student, fitness) | 5 |

Each page has metadata: `name`, `category`, `added_value` (1-5), `pages`, `repeatable`, `dependencies`.

---

## 4. Project architecture

```
agenda_gen/
├── main.py                  # Entry point (CLI)
├── config.yaml              # Sample configuration
├── requirements.txt
├── agenda/
│   ├── __init__.py
│   ├── config.py            # Parameter loading and validation
│   ├── sizes.py             # Page size dictionary
│   ├── catalog.py           # Registry of available pages
│   ├── calendar.py          # Date calculations (weeks, months, holidays)
│   ├── grid.py              # Layout grid: columns, baseline, rulers (mm)
│   ├── tokens.py            # Design tokens: spacing scale, type scale, strokes
│   ├── draw.py              # Drawing helpers on top of fpdf2 (lines, boxes, patterns)
│   ├── themes.py            # Colors, fonts
│   ├── assembler.py         # Final page order, padding and booklets
│   ├── imposition.py        # Reordering for booklet printing
│   ├── exporter.py          # PDF writing (fpdf2), bookmarks and internal links
│   └── pages/
│       ├── base.py          # BasePage base class
│       ├── core.py
│       ├── optional.py
│       └── value_added.py
├── assets/
│   ├── fonts/
│   └── icons/
├── tests/
└── output/
```

### Recommended libraries

| Library | Use |
|---|---|
| `fpdf2` | Drawing PDF pages in mm, TTF fonts, text wrapping, links, bookmarks, SVG icons |
| `pypdf` | Imposition (placing 2 pages per sheet side) |
| `PyYAML` | Configuration file |
| `holidays` | Holidays by country |
| `qrcode` + `Pillow` | QR codes |
| `PySide6` | GUI: settings, live preview, section bar |
| `pypdfium2` | Rasterising pages for the GUI preview |
| `typer` or `argparse` | Command line |
| `pydantic` | Configuration validation |

---

## 5. Code design (key classes)

### 5.1 Page base class

```python
class BasePage:
    id = ""
    name = ""
    category = ""           # core | optional | value_added
    section = ""            # GUI section bar: front_back | monthly | weekly | daily | optional | value_added
    added_value = 1
    pages = 1               # pages taken per instance

    def __init__(self, config):
        self.config = config

    def instances(self):
        """Returns a list of contexts (e.g. 12 months, 52 weeks)."""
        return [{}]

    def draw(self, pdf, ctx, grid):
        """Draws on the current page of 'pdf' (fpdf2), positioned with 'grid' (safe zone, in mm)."""
        raise NotImplementedError
```

### 5.2 Automatic registration (decorator)

```python
CATALOG = {}

def register(cls):
    CATALOG[cls.id] = cls
    return cls

@register
class Monthly(BasePage):
    id = "monthly"
    name = "Monthly planner"
    category = "core"
    pages = 1

    def instances(self):
        return [{"month": m} for m in range(1, 13)]

    def draw(self, pdf, ctx, grid):
        ...
```

Adding a new page = creating a class with `@register`. The rest of the code is untouched.

### 5.3 Page sizes

All measurements are in millimetres. The document is created with `FPDF(unit="mm", format=(139.7, 215.9))`, so every coordinate in code is the real printed measurement and no unit conversion is needed. Font sizes are still given in points.

```python
SIZES = {
    "half_letter": (139.7, 215.9),
    "a5": (148, 210),
    "b6": (125, 176),
    "letter": (215.9, 279.4),
    "a4": (210, 297),
}
```

Custom sizes supported: `--size 150x200` (in mm).

### 5.4 Alternating margins (important for printing)

Odd and even pages have the inner margin on opposite sides:

```python
def safe_area(page_number, cfg):
    inner, outer = cfg.inner_margin, cfg.outer_margin
    if page_number % 2 == 1:     # right-hand page
        left, right = inner, outer
    else:                        # left-hand page
        left, right = outer, inner
    return left, right
```

---

## 6. Booklet logic (variable parameter)

### 6.1 Rules

- **Folded (default):** 1 sheet folded in half = 4 pages (saddle-stitched booklet), and each booklet's page count must be a multiple of 4.
- **Flat (selectable):** 1 sheet = 2 pages (plain double-sided printing).
- Default booklet: **5 folded sheets = 20 pages**.
- Imposition only applies to folded booklets.

### 6.2 Calculation

```python
import math

def pages_per_booklet(value, unit, folded=True):
    if unit == "sheets":
        return value * (4 if folded else 2)
    return value

def plan_booklets(total_pages, booklet_pages):
    n = math.ceil(total_pages / booklet_pages)
    padding = n * booklet_pages - total_pages
    return n, padding
```

### 6.3 Padding leftover pages

The pages missing to complete the last booklet are automatically filled with **notes** pages (or with value-added pages chosen by the user, e.g. gratitude or ideas). Parameter: `pad_with: notes`.

### 6.4 Imposition (optional)

For a folded booklet, the print order of each N-page booklet is:

```python
def imposition_order(n):
    """n is a multiple of 4. Returns page pairs per sheet side."""
    sides = []
    for i in range(n // 4):
        sides.append((n - 2*i, 2*i + 1))       # front
        sides.append((2*i + 2, n - 2*i - 1))   # back
    return sides
```

The `imposition.py` module takes the ordered PDF and produces another one with 2 pages per side on landscape letter/A4, ready to print double-sided and fold.

---

## 7. Execution flow

1. **Read configuration** (YAML + CLI, CLI takes precedence).
2. **Validate** parameters (size, existing pages, dependencies).
3. **Select pages** (list by IDs, categories or the GUI).
4. **Expand instances** (12 months, 52 weeks, etc.).
5. **Order** following a logical sequence:
   `cover → personal_info → goals → yearly → [monthly → per week: weekly spread → that week's daily pages] → optional → value-added → notes → contacts → back_cover`
6. **Compute booklets** and pad with notes.
7. **Draw** each page with `fpdf2`, positioned on the layout grid, adding bookmarks (`start_section`) and internal links (`add_link`).
8. **(Optional)** Apply imposition (`pypdf`) and crop marks.
9. **Export PDF** and show a summary (total pages, sheets, booklets, padding).

---

## 8. User interface

### 8.1 Command line

```bash
# Defaults (half letter, 5-sheet booklet, core pages)
python main.py

# Custom selection
python main.py --pages cover,personal_info,monthly,weekly,habits,health,qr \
               --size a5 --booklet 8 --unit sheets --year 2027

# All pages in a category
python main.py --category core,optional

# With imposition for binding
python main.py --imposition --crop-marks

# List the catalog with value-added scores
python main.py --list
```

### 8.2 GUI

Desktop window (PySide6) with a settings panel, a live preview (single page, facing spread or imposed sheet) and a **color-coded section bar** showing every generated page by section, with booklet boundaries. Full spec: [gui.md](../architecture/gui.md).

- Settings form generated from the same config model as the CLI and YAML.
- Page checklist grouped by category with its value score.
- The preview renders only the visible pages, so it updates while you change settings.
- The section bar and summary (pages, sheets, booklets, padding) update instantly. Click the bar to jump to a page.

### 8.3 `config.yaml` file

```yaml
page_size: half_letter
booklet:
  size: 5
  unit: sheets
  folded: true
year: 2027
week_start: monday
holiday_country: CR
planners: [weekly, daily]
notes_pattern: dotted
pad_with: notes
pages:
  - cover
  - personal_info
  - yearly
  - monthly
  - weekly
  - habits
  - health
  - qr
  - notes
  - contacts
  - back_cover
```

---

## 9. Page details (design specification)

| Page | Content / design |
|---|---|
| Cover | Title, year, name; theme color; optional logo (PNG) |
| Personal information | Lined fields: name, phone, email, address, emergency contact, blood type |
| Yearly | 12 mini calendars in a 3x4 grid, weekends highlighted |
| Monthly | Day grid, notes/priorities column, month name |
| Weekly (WO2P) | Left page: Mon–Wed + priorities; right page: Thu–Sun + notes |
| Daily | Date, hourly schedule, tasks, notes |
| Notes | Configurable pattern (lined, dotted, grid) with spacing in mm |
| Contacts | Table: name, phone, email, note |
| Goals | 5–6 goals with steps, deadline and checkboxes |
| Habits | 31 days x N habits grid with circles |
| Budget | Income, fixed/variable expenses, savings, total |
| Health | Tracker for water (glasses), sleep (hours), mood (emojis or circles) |
| Meals | Weekly menu + grocery list with checkboxes |
| Gratitude | 3 slots per day or per week |
| 30-day challenges | 30-box grid with challenge title |
| Travel | Destination, dates, budget, itinerary, packing list |
| QR | Generated from user URLs with a label |
| Vision board | Empty frames with areas to paste photos and quotes |

---

## 10. Development phases

| Phase | Deliverable | Estimated duration |
|---|---|---|
| **1. Foundation** | Project structure, configuration, page sizes, alternating margins | 1–2 days |
| **2. Calendar** | Date module, weeks, holidays | 1 day |
| **3. Core pages** | Cover, personal info, yearly, monthly, weekly, daily, notes, contacts | 3–4 days |
| **4. Booklets** | Calculation, automatic padding, validation | 1–2 days |
| **5. Optional pages** | 10 optional pages | 3 days |
| **6. Value-added** | 12 special pages + QR | 4 days |
| **7. Interface** | CLI, YAML | 1 day |
| **7b. GUI** | Settings panel, live preview, section bar, export | 4–5 days |
| **8. Imposition** | Booklet order, crop marks | 2 days |
| **9. Testing and polish** | Real print tests, themes, adjustments | 2–3 days |

**Approximate total:** 4–5 weeks part-time.

Progress is tracked per phase in [phases.md](phases.md).

---

## 11. Testing

- **Unit:** booklet calculation, padding, weeks of the year (leap years), imposition.
- **Visual:** generate a sample PDF for each size and check nothing spills past the margins.
- **Real print:** paper test at the final size, verifying the binding margin.
- **Edge cases:** a single page, 1-sheet booklet, extreme sizes, leap year.

---

## 12. Future extensions

- Custom color themes and fonts.
- Export a digital version with hyperlinks between months and weeks.
- Niche templates (student, entrepreneur, fitness) with a single command.
- Generate stickers and dividers as separate PDFs.
- Double-sided printing support with mirrored back side.

---

## 13. Next steps

Resolved: booklets are folded by default (selectable); both weekly and daily planners; holidays default to Costa Rica (`CR`); rendering with fpdf2 ([ADR 0001](../decisions/0001-pdf-rendering-fpdf2.md)).

1. Define the layout grid and design tokens ([layout-grid.md](../architecture/layout-grid.md)).
2. Start with **Phases 1 and 3** to get a first working agenda.
