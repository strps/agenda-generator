# GUI: Configuration, Live Preview and Section Bar

A desktop window to configure the agenda, preview pages as they will print, and see the structure of the whole agenda in a color-coded bar.

## 1. Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ [Open config] [Save config]                       [Export PDF ▸]     │
├────────────────────┬─────────────────────────────────────────────────┤
│ Settings           │  ◀  Spread 72–73 of 498   [Single|Spread|Sheet] ▶│
│ ─ Page size        │  ┌───────────────┬───────────────┐              │
│ ─ Booklets         │  │               │               │              │
│   size / unit /    │  │   left page   │  right page   │              │
│   folded           │  │               │               │              │
│ ─ Year, week start │  │               │               │              │
│ ─ Planners         │  └───────────────┴───────────────┘              │
│ ─ Pages (checklist │  zoom [ fit ▾ ]                                 │
│   by category)     │                                                 │
│ ─ Theme, margins   │                                                 │
├────────────────────┴─────────────────────────────────────────────────┤
│ Front│Monthly│Weekly│Daily│Weekly│Daily│ … │Optional│Value│Back│pad  │ ← section bar
│ ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    ┆    │ ← booklet ticks
│ ■ Front/back 6  ■ Monthly 12  ■ Weekly 106  ■ Daily 365  ■ Optional 18 … │ ← legend + counts
│ 498 pages · 125 sheets · 25 booklets · 2 padding pages                 │ ← summary
└──────────────────────────────────────────────────────────────────────┘
```

- **Tooltips:** every toolbar control has a detailed tooltip, with texts in `agenda/gui/help_text.py` (`TOOLTIPS`). This covers Open/Save config, Export PDF, prev/next, the Single/Spread/Sheet buttons and zoom. When the config is invalid, the Export tooltip also gives the reason it is disabled. A "debug grid" checkbox is not implemented.
- **Settings panel (left):** generated from the same pydantic config model used by the CLI and YAML, so the three never drift apart. Loads and saves `config.yaml`.
- **Preview (center):** three modes.
  - *Single:* one page.
  - *Spread:* left + right pages as they face each other when bound (the default; the way to check WO2P layouts and alternating margins).
  - *Sheet:* the imposed printer sheet (only when booklets are folded).
- **Section bar (bottom):** described in section 3.
- **Export:** writes the full PDF in a background thread with a progress bar.

## 2. Architecture

The GUI is a thin layer over the core library. The core has no GUI imports.

```
agenda/
├── ...                      # core (config, assembler, pages, exporter)
└── gui/
    ├── app.py               # Main window, wiring
    ├── settings_panel.py    # Form built from the config model
    ├── preview.py           # Page/spread/sheet viewer, zoom, cache
    ├── section_bar.py       # Color-coded bar, ticks, legend, navigation
    └── workers.py           # Background rendering/export threads
```

It depends on two core functions:

- `build_plan(config) -> PagePlan`: the ordered list of `(page_class, ctx, page_number, side, booklet_index, section)`. It is fast because nothing is drawn, so it runs on **every** settings change and immediately updates the section bar and summary.
- `render_pages(config, plan, indices) -> bytes`: draws only the requested pages with fpdf2 and returns PDF bytes. Each page keeps its real page number, so margins and left/right sides are correct.

### Preview pipeline

1. A settings change (debounced ~300 ms) calls `build_plan`, which updates the bar right away.
2. The preview asks for the visible pages (1, 2 or one imposed sheet) via `render_pages` in a worker thread.
3. **pypdfium2** rasterises the PDF bytes to images at the current zoom.
4. Images are cached by `(config hash, page index, zoom)`. Changing the year invalidates everything; navigating does not.

Rendering a single spread instead of ~500 pages keeps the preview interactive.

### Libraries

| Library | Use |
|---|---|
| `PySide6` (Qt, LGPL) | Window, widgets, custom-painted section bar, threads |
| `pypdfium2` | Rasterising PDF pages for the preview (permissive license, pip-installable) |

PyMuPDF would also work for rasterising, but it is AGPL-licensed, which matters if the tool is ever sold. NiceGUI (web-based UI in the browser) is a lighter alternative to PySide6 if a browser UI is preferred.

## 3. Section bar

### What it shows

- **One segment per page, in agenda order.** The width is proportional to the page count (≈2 px per page at 500 pages on a 1000 px bar), so the bar is a scaled map of the physical agenda.
- **Consecutive pages of the same section merge** into one segment. A **2 px gap** separates segments of different sections. The gap is required, not decorative (see 3.3).
- **Booklet ticks** under the bar mark where each booklet starts.
- **A position marker** shows the spread currently in the preview.
- **A legend** lists every section shown, with a swatch, name and page count, plus a one-line summary (pages, sheets, booklets, padding). Hovering a swatch, a section button or the "Legend:" title explains what the color means (`help_text.section_tooltip`); the padding swatch carries the same 45-degree hatch as the bar.

### Sections and colors

Each page class declares a `section` attribute. The assembler copies it into the `PagePlan`.

| Section | Pages | Light | Dark |
|---|---|---|---|
| Front & back matter | cover, personal_info, goals, yearly, notes, contacts, back_cover | neutral gray `#8a8984` | `#8a8984` |
| Monthly | monthly | blue `#2a78d6` | `#3987e5` |
| Weekly | weekly | orange `#eb6834` | `#d95926` |
| Daily | daily | aqua `#1baf7a` | `#199e70` |
| Optional | optional category | violet `#6250d6` | `#9085e9` |
| Value-added | value-added category | yellow `#eda100` | `#c98500` |
| Padding | auto-inserted filler pages | gray with 45° hatch | same |

Colors come from the validated reference palette (dataviz skill). The assignment was chosen by checking **every pair of sections that can sit next to each other** in the bar, in both light and dark mode:

- With default settings, every bordering pair passes the colorblind separation target (ΔE ≥ 8) and the normal-vision floor (ΔE ≥ 15). This includes monthly↔weekly↔daily, which alternate constantly.
- Two pairs fall short. Both only meet in unusual configurations:
  - Monthly next to optional (only when weekly and daily are both turned off).
  - Weekly next to value-added (only when daily and optional are both turned off).

  The 2 px gap, the legend and the hover tooltip still distinguish them.
- Seven hues can't all be told apart from each other, so front and back matter use neutral gray instead of a hue. They are at opposite ends of the bar and never meet each other.

### Interaction

- **Hover:** a tooltip appears for the page under the cursor, e.g. `Page 143 · Weekly · Week 12 (Mar 16–22) · Booklet 8, sheet 2`. The hit area is the full bar height, not just the page's 2 px.
- **Click:** jumps the preview to that page's spread. **Drag:** scrubs through pages.
- **Keyboard:** arrow keys move by spread, Page Up/Down by booklet, Home/End to the start/end.
- **Legend click:** jumps to the first page of that section.

### Accessibility

- Identity is never color alone. The legend is always shown, the tooltip names the section, and section names are drawn inside segments wide enough to fit them.
- Padding uses a hatch pattern as well as gray.
- Text (legend labels, counts, tooltip) uses normal text colors, never the section color. The colored swatch carries identity.
- Light and dark values are separate validated steps that follow the system theme. They are not an automatic inversion.

## 4. Open questions

- Should the preview show a fake "paper" background and drop shadow, or the bare page?
- Should page selection in the settings panel be drag-to-reorder, or keep the fixed logical order?
