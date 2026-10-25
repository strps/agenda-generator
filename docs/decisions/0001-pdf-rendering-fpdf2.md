# ADR 0001: Draw pages directly to PDF with fpdf2

- **Status:** Accepted
- **Date:** 2026-10-25

## Context

The agenda is a print-ready PDF of ~500 pages with precise, millimetre-based layouts, alternating margins, internal links and bookmarks.

## Decision

Use **fpdf2** to draw every page directly into the PDF. Use **pypdf** only for imposition (placing 2 pages on each sheet side).

A spike with fpdf2 2.8.9 on 2026-10-25 confirmed:

- `FPDF(unit="mm", format=(139.7, 215.9))` gives an exact half-letter page.
- TTF fonts are embedded as subsets with full Unicode (accents included), via `add_font`.
- `multi_cell` wraps text automatically and `get_string_width` measures text in mm.
- `add_link` / `set_link` create internal links, and `start_section` creates PDF bookmarks.
- `image()` accepts SVG files, so vector icons and decorations can still be used.

## Why

- A single pure-Python dependency writes the PDF directly, with no conversion step.
- Native mm units, text wrapping and text measurement cover the layout-grid needs.
- Links and bookmarks are available while drawing, without post-processing.

## Alternatives considered

| Option | Why not chosen |
|---|---|
| SVG pages + `cairosvg` conversion | Worked in a spike, but adds a conversion step and manual text measuring. Dropped in favour of a simpler stack. |
| `reportlab` | Capable, but more verbose. fpdf2 covers the same needs with a simpler API. |
