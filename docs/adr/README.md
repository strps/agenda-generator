# Architecture decisions

Append-only. Agents read this index and open an ADR only when their work touches
its area. A changed decision gets a NEW ADR; the old one is marked superseded.

<!-- one line per ADR: - [NNNN](NNNN-slug.md) <title> — <Accepted | Superseded by NNNN> — area: <modules/paths> -->
- [0001](0001-config-fields-single-source.md) Config fields are the single source of help text and CLI flags — Accepted — area: agenda/config, agenda/fields.py, agenda/gui/help_text.py, agenda/cli.py
- [0002](0002-page-package-import-order.md) Page package import order is catalog registration order — Accepted — area: agenda/pages/value_added/, agenda/pages/optional/, agenda/catalog
- [0003](0003-gui-test-marker.md) Qt tests carry the `gui` pytest marker — Accepted — area: tests/, tests/conftest.py, pyproject.toml
- [0004](0004-flat-config-and-section-grouping.md) Config stays flat; section grouping lives only in agenda/templates.py — Accepted — area: agenda/config, agenda/configfile, agenda/templates.py
