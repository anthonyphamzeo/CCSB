# US-070-T02: Implement permission profiles and assignments

- Status: Completed
- Evidence basis: Direct database-model schema evidence plus static schema/seed validation
- Reviewed: 2026-07-13

## Accepted outcome

`ccsb_permissionprofile` and `ccsb_permissionassignment` define action flags, principal identity, board/location/group scope, effective assignment windows, explicit grant/deny access effects, and restrictive product-level access behavior.

Profiles and assignments remain subordinate to Dataverse security: they express CCSB product scope and cannot bypass table, row, team, business-unit, sharing, or field-security checks.

## Evidence

- `tools/provisioning/CCSB.FoundationSchema/schema/ccsb.foundation.schema.json`
- `tests/Fixtures/Schema/US-004-T09-seed-manifest.json`
- `tools/validation/security/US-070-T02-static-validator.py`
- `docs/implementation/testing/evidence/US-070-T02/static-report.md`
- `docs/design/data-model/physical-schema/`
- `docs/tracking/status/dbmodel-review/ccsb-dbmodel-task-status-overlay.csv`

## Boundary

Runtime authorization logic remains `US-070-T03`. Permission-aware UI behavior remains `US-070-T04`. Connected positive and negative role tests remain `US-070-T05`. Managed-solution role/security packaging remains `US-070-T06`.
