# Layout Grid and Design Tokens

All pages are positioned with the same grid and spacing system so the design stays consistent. Every value is in **millimetres**, matching fpdf2's `unit="mm"` (see [ADR 0001](../decisions/0001-pdf-rendering-fpdf2.md)).

## 1. Page frame

```
┌──────────────────────────────┐  ← trim (page edge)
│  bleed (3 mm, only with      │
│  crop_marks)                 │
│ ┌──────────────────────────┐ │
│ │ header band              │ │  ← safe area starts at the margins
│ ├──────────────────────────┤ │
│ │                          │ │
│ │ content: columns ×       │ │
│ │ baseline rows            │ │
│ │                          │ │
│ ├──────────────────────────┤ │
│ │ footer band (page no.)   │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
  inner/outer margins alternate on left/right pages
```

- **Margins:** `inner_margin` 15 mm (binding side), `outer_margin` 10 mm, top 10 mm, bottom 10 mm. Left and right swap on even/odd pages.
- **Header band:** fixed height (e.g. 12 mm) for the page title, month and date.
- **Footer band:** fixed height (e.g. 6 mm) for page numbers and month tabs.

## 2. Grid

- **Columns:** 6 columns with a 3 mm gutter inside the safe area. Six divides cleanly into 1, 2, 3 and 6 (e.g. the weekly spread: 3 days per page = 2 columns each).
- **Baseline:** a 5 mm baseline (a comfortable handwriting line height). Lines, dot grids, table rows and text baselines all snap to it, so writing lines align across pages and across a spread.
- **Snapping:** layout helpers return positions aligned to columns and baselines (`grid.col(2)`, `grid.row(5)`, `grid.span(cols=3, rows=8)`). Pages never use raw coordinates.

The column count, gutter and baseline are configurable per theme. A 4 mm baseline gives a denser layout, for example.

## 3. Design tokens

Defined once in `tokens.py`. Colors come from the `themes.py` palette (plus per-color overrides) carried on each document (`pdf.agenda_palette`, read with `draw.color`); `tokens.COLORS` is never mutated, so threaded previews stay independent:

| Token | Example values |
|---|---|
| Spacing scale | 1, 2, 3, 5, 8, 13 mm |
| Type scale | 6, 7.5, 9, 12, 18, 28 pt |
| Stroke widths | hairline 0.15 mm, light 0.25 mm, regular 0.4 mm |
| Colors | ink, muted ink, line gray, accent, weekend/holiday tint |
| Corner radii | 0, 1, 2 mm |
| Dot size (dotted pattern) | 0.35 mm |

fpdf2 takes font sizes in points even when `unit="mm"`. To align text to the baseline grid, convert with `mm = pt × 25.4 / 72`.

## 4. Rulers and debug overlay

A `--debug-grid` flag draws an overlay on every page: margins, columns, baseline lines, bleed and the safe area, plus mm rulers along the top and left edges. It's used to check alignment on screen and on a test print. The overlay is drawn only when the flag is set, so it never reaches production output.
