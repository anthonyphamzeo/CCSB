# US-002-T04: Design administrator diagnostics

- Status: In Progress
- Owner:
- Branch:
- Target release: Release 01 MVP
- Dependencies: US-004; US-002-T01; US-002-T02; US-002-T03
- Started: 2026-07-13
- Planned validation: `python tools/validation/compatibility/US-002-T04-static-validator.py`
- Blockers: Connected Dataverse UX provisioning and Custom API registration remain pending.
- Static validation: Pass

## Implemented

Started the administrator compatibility diagnostics UX contract for configuration administration. The design surfaces compatibility state, open blocking diagnostics, affected records and fields, migration/remediation actions, runtime projection health, validation operation evidence, and a safe re-validation command.

## Remaining Definition-of-Done gate

Provision the actual model-driven form/view/command surface or Configuration Studio equivalent in Dataverse and prove administrators can revalidate without activating or reading server logs.

## Evidence

- `docs/design/ux/compatibility/US-002-T04-administrator-diagnostics.md`
- `docs/design/ux/compatibility/US-002-T04-administrator-diagnostics.json`
- `tools/validation/compatibility/US-002-T04-static-validator.py`
- `docs/implementation/testing/evidence/US-002-T04/static-report.md`