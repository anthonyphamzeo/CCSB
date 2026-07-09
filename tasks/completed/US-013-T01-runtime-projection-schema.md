# US-013-T01: Define runtime projection schema

- Status: Completed
- Evidence basis: Direct database-model schema evidence
- Reviewed: 2026-07-09

## Accepted outcome

The versioned `ccsb_runtimeprojection` schema defines payload JSON, projection schema version, source change token, content hash, generation timestamp, status, scope, and sizing fields without storing secrets.

## Evidence

- `docs/design/data-model/physical-schema/`
- `docs/tracking/status/dbmodel-review/ccsb-dbmodel-task-status-overlay.csv`

Generator, validation, and import hooks remain separate tasks.
