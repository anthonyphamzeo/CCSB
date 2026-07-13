# US-070-T01: Define permission model and matrix

- Status: Completed
- Evidence basis: Static security model, machine-readable permission matrix, and validator report
- Reviewed: 2026-07-13

## Accepted outcome

The CCSB permission model defines action flags, scope dimensions, least-privilege personas, Dataverse prerequisite checks, field-security treatment, least-disclosure denial behavior, and negative cases for admin, scheduler, publisher, support, and unauthorised personas.

CCSB permissions are explicitly restrictive: Dataverse table, row, and field access must pass before any CCSB profile or assignment can allow an action.

## Evidence

- `docs/design/security/US-070-T01-permission-model-and-matrix.md`
- `tests/Fixtures/Security/US-070-T01-permission-matrix.json`
- `tools/validation/security/US-070-T01-static-validator.py`
- `docs/implementation/testing/evidence/US-070-T01/static-report.md`

## Boundary

Runtime authorization enforcement remains `US-070-T03`. Permission-aware PCF/model-driven actions remain `US-070-T04`. Connected positive and negative role tests remain `US-070-T05`. Managed-solution security role packaging remains `US-070-T06`.
