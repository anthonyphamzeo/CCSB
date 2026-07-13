# US-070-T02 Static Permission Schema Validation Report

**Status:** PASS
**Generated:** 2026-07-13T08:33:25Z
**Schema:** `tools/provisioning/CCSB.FoundationSchema/schema/ccsb.foundation.schema.json`
**Seed manifest:** `tests/Fixtures/Schema/US-004-T09-seed-manifest.json`
**Permission matrix:** `tests/Fixtures/Security/US-070-T01-permission-matrix.json`

## Counts

- Permission profile fields: 16
- Permission assignment fields: 11
- Profile action flags: 10
- Permission relationships: 5
- Seed profiles: 1
- Seed assignments: 1
- T01 matrix flags covered: 0
- Errors: 0
- Warnings: 0

## Validation Scope

- `ccsb_permissionprofile` table presence, ownership, profile code key, profile type, scope mode, enabled flag, and action flags
- `ccsb_permissionassignment` table presence, ownership, principal fields, access effect, scope type, effective dates, approval reference, and enabled flag
- Board-version, profile, board, location, and group-node scope relationships
- Deterministic seed coverage for profile and assignment rows
- Continuity with the US-070-T01 action matrix profile flags when the matrix is present on the branch
- No secret/token/password/connection-string fields in permission schema

## Issues

- None

## Boundary

This report proves the static schema and seed contract for US-070-T02. Runtime authorization logic remains US-070-T03, permission-aware UI behavior remains US-070-T04, connected role-matrix tests remain US-070-T05, and managed-solution role packaging remains US-070-T06.
