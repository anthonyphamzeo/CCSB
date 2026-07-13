# US-070-T01 Static Permission Matrix Validation Report

**Status:** PASS
**Generated:** 2026-07-13T08:18:46Z
**Matrix:** `tests/Fixtures/Security/US-070-T01-permission-matrix.json`

## Counts

- Personas: 5
- Actions: 12
- Scope dimensions: 7
- Mutating Custom API-governed actions: 9
- Negative cases: 11
- Diagnostic codes: 8
- Errors: 0
- Warnings: 0

## Validation Scope

- Required admin, scheduler, publisher, support, and unauthorised personas
- Coverage for every `ccsb_permissionprofile` action flag from US-070-T02
- Dataverse-first authorization order and CCSB restrictive permission rule
- Scope dimensions for board, board version, group, location, resource, time, and field policy
- Negative cases for Dataverse denial, field security, missing profile, inactive assignment, forged scope, publish, rollback, support redaction, and direct mutation
- Stable diagnostic catalog and least-disclosure denial policy

## Issues

- None

## Boundary

This report proves the US-070-T01 design and static matrix contract. Runtime authorization enforcement remains US-070-T03, permission-aware UI behavior remains US-070-T04, connected positive/negative role tests remain US-070-T05, and managed-solution role packaging remains US-070-T06.
