# ADR 0009: The back cover is optional and off by default

- Status: Accepted
- Date: 2026-11-26
- Plan: 2026-11-25-text-fit-warnings (text-fit-warnings/09)

## Context
build_plan always appended a back cover, and listing back_cover in `pages` had no effect. The user
asked for the back cover to be optional and off unless requested.

## Decision
- Config.back_cover (bool, default False) is the single switch for BackCover in build_plan; membership
  of "back_cover" in `pages` stays ignored (like cover and personal_info).
- This is an intentional exception to the rule that every existing config.yaml loads to the same
  Config and output: configs without the key now produce no back cover.
- With separate_covers, the inside-back filler and back cover sit outside the booklets only when
  back_cover is on (2 trailing outside pages); otherwise only cover + inside-cover filler are outside
  and the inner block runs to the last page. Padding precedes the back cover when it exists.

## Consequences
Code and tests that expect BackCover last must set back_cover=True. Changes to padding or separate
covers in agenda/assembler.py must handle both tails (0 or 2 outside trailing pages).
