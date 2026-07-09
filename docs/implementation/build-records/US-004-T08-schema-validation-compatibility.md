# US-004-T08 - Schema Validation and Compatibility Checks

## Implementation Scope

The latest Foundation Schema provisioner now includes a fail-closed live Dataverse metadata compatibility gate. Normal provisioning runs the gate after metadata creation/update and before publish/export. Operators can also run the same gate without changes using `-ValidateLiveOnly`.

## Checks Covered

- Solution compatibility: expected unmanaged solution and version `1.0.0.1`.
- Table compatibility: required table presence and ownership model.
- Field compatibility: required fields, required level, Dataverse type, string/memo length, numeric ranges, decimal precision, boolean defaults, and choice option values.
- Relationship compatibility: lookup field presence/type, lookup target table, relationship existence, one-to-many/many-to-one cardinality, endpoint match, and Delete Restrict behavior.
- Schema contract: static validation confirms schema version `1.0.0`, validation result evidence fields, board-version/operation evidence relationships, live-gate rule markers, and Core/Foundation logical-name collision handling.

## Diagnostics

Validation emits stable `CCSB-SCHEMA-*` diagnostic codes with table, field, relationship, expected value, actual value, and message fields. Use `-CompatibilityReportPath` or `--compatibility-report` to write JSON release evidence.

Example:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org.crm.dynamics.com" `
  -Username "admin@tenant.onmicrosoft.com" `
  -ValidateLiveOnly `
  -CompatibilityReportPath "out\foundation-schema-compatibility.json"
```

## Boundary

This completes the live metadata compatibility gate for the schema package. Board-version activation Custom API enforcement and administrator diagnostics UX remain downstream tasks under US-002/US-010 because that runtime layer is not present in this repo.
## Core/Foundation Collision Resolution

A DEV run showed the Core **Schedule Board** dependency resolving to `ccsb_board`. The foundation Board Registry table has therefore been renamed to `ccsb_boardregistry`, and the lookup from the Core Schedule Board table to the registry now uses `ccsb_boardregistryid` so it does not collide with the Core table primary key `ccsb_boardid`. This allows the Core `ccsb_board` table and the foundation registry table to coexist safely.