# US-002-T02: Add compatibility metadata

- Status: In Progress
- Static validation: Pass
- Reviewed: 2026-07-09

## Implemented

Board-version and runtime-projection metadata fields, migration/compatibility choices, invariants, diagnostics, and an idempotent backfill contract.

## Remaining Definition-of-Done gate

Execute the connected Dataverse backfill and prove every active board/current projection has unambiguous metadata.

## Evidence

- `docs/design/data-model/compatibility/US-002-T02-compatibility-metadata.md`
- `docs/implementation/testing/evidence/US-002-T02/static-report.md`
