# ADR 0004: Config stays flat; section grouping lives only in agenda/templates.py

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-structure-cleanup (structure-cleanup/01, carried from earlier plans)

## Context
Settings are shown and saved in grouped sections, but Config is used everywhere as one flat model.
Nested sub-models were explicitly kept out of scope.

## Decision
Config stays flat. YAML blocks are flattened in configfile.flatten; save_yaml writes the grouped
form. agenda/templates.py imports no Config/pydantic and is the only source of section grouping.
tests/test_sample_files.py pins config.yaml to the flat sample.

## Consequences
Every existing config.yaml must keep loading to the same Config. Grouping changes happen in
templates.py only; introducing nested Config models needs a new ADR superseding this one.
