# US-004-T09 Static Integrity Report

**Status:** PASS
**Generated:** 2026-07-09T11:52:55Z
**Manifest:** `tests/Fixtures/Schema/US-004-T09-seed-manifest.json`

## Counts

- Seed records: 26
- Entity coverage: 24 entities
- Negative fixtures: 7
- Errors: 0
- Warnings: 0

## Entity Coverage

- `ccsb_board`
- `ccsb_boardregistry`
- `ccsb_boardversion`
- `ccsb_entitydefinition`
- `ccsb_fieldmapping`
- `ccsb_location`
- `ccsb_operation`
- `ccsb_operationaudit`
- `ccsb_operationitem`
- `ccsb_outboxevent`
- `ccsb_permissionassignment`
- `ccsb_permissionprofile`
- `ccsb_publishlock`
- `ccsb_publishsnapshot`
- `ccsb_publishsnapshotitem`
- `ccsb_relationshipmapping`
- `ccsb_resource`
- `ccsb_resourcecapability`
- `ccsb_resourcerole`
- `ccsb_runtimeprojection`
- `ccsb_schedulechange`
- `ccsb_scheduleitem`
- `ccsb_scheduleversion`
- `ccsb_statusmodel`

## Validation Scope

- Manifest header and fixed clock
- Schema-aligned entities, fields, required fields, types, ranges, and choice values
- Relationship lookup targets and required lookup presence
- Deterministic seed-key uniqueness
- Active board-version lifecycle and immutability
- Current runtime projection validity
- Publish snapshot, audit, lock, rollback, and retention assertions
- Required negative fixture coverage

## Issues

- None

## Boundary

This is a static seed-contract validation. Live Dataverse upsert, teardown, credential handling, and CI environment scheduling remain deployment work.
