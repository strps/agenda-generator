# ADR 0002: Page package import order is catalog registration order

- Status: Accepted
- Date: 2026-10-26
- Plan: 2026-10-26-structure-cleanup (structure-cleanup/06, structure-cleanup/07)

## Context
Pages register themselves via @register at import time, so the catalog order is the import order.
Splitting value_added.py and optional.py into packages put that order in each __init__.py.

## Decision
agenda/pages/value_added/__init__.py and agenda/pages/optional/__init__.py import their page modules
in the original class order and re-export all public names; shared helpers live in _common.py.
Since ruff I001 is enabled, the first import carries `# noqa: I001` with a comment.
tests/test_catalog_order.py pins the ordered page ids and every preset's page list.

## Consequences
Never let an import sorter reorder those files. An edit needed in test_catalog_order.py means the
order changed, which is a bug unless the change is intended. catalog.PAGE_MODULES is unchanged.
