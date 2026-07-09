# US-044-T01: Implement status models and transitions

- Status: Completed
- Evidence basis: Direct database-model schema evidence
- Reviewed: 2026-07-09

## Accepted outcome

`ccsb_statusmodel`, `ccsb_statusdefinition`, and `ccsb_statustransition` define scoped status keys, labels, categories, transition reasons/permissions, and board-version configuration.

## Evidence

- `docs/design/data-model/physical-schema/`
- `docs/tracking/status/dbmodel-review/ccsb-dbmodel-task-status-overlay.csv`

Command-service transition enforcement remains separate work.
