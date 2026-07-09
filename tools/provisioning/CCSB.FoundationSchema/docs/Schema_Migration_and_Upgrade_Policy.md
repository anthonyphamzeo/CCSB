# Schema Migration and Upgrade Policy

This runbook supports US-004-T10 for the CCSB Foundation Schema package.

## Package Boundary

- Source build: `1.0.0.6`
- Dataverse solution unique name: `ccsb_foundationschema`
- Dataverse solution version: `1.0.0.1`
- Schema contract: `1.0.0`
- DEV layer: unmanaged solution only
- TEST/UAT/production layer: managed solution package only

## Export Packages

Validate without changes:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org.crm.dynamics.com" `
  -Username "user@tenant.onmicrosoft.com" `
  -ValidateLiveOnly `
  -CompatibilityReportPath "out\foundation-schema-compatibility.json"
```

Export the unmanaged DEV package:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org.crm.dynamics.com" `
  -Username "user@tenant.onmicrosoft.com"
```

Export the managed package for TEST/UAT/production rehearsal:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org.crm.dynamics.com" `
  -Username "user@tenant.onmicrosoft.com" `
  -ExportManaged `
  -CompatibilityReportPath "out\foundation-schema-compatibility.json"
```

The default managed output is `out\CCSB_FoundationSchema_1_0_0_1_managed.zip`.

## Additive Change Rules

- Add metadata; do not delete, rename, repurpose, or shrink released metadata.
- Add optional fields first. Tighten requiredness only after backfill and validation evidence exists.
- Append choice options only. Never reuse existing numeric values for a different meaning.
- Introduce alternate keys before runtime writes depend on them and resolve duplicate data first.
- Keep previous projection schema versions readable during the compatibility period.

## Destructive Change Prohibition

- Do not delete, rename, repurpose, or shrink released metadata.
- Do not change relationship delete behavior away from Restrict for board, version, projection, publish, audit, lock, schedule-change, or outbox records.
- Do not mutate immutable active board versions, publish snapshots, snapshot items, audit rows, outbox events, or rollback images.

## Backfill Rules

- Run backfill after managed import and before feature activation.
- Keep active board versions immutable; clone to Draft for configuration normalization.
- Do not rewrite publish snapshots, snapshot items, operation audit rows, outbox rows, rollback images, or historical schedule-change evidence.
- Make every backfill idempotent and scoped by board, board version, schedule version, projection, or source key.
- Record operation/audit evidence with package version, counts, failures, correlation ID, and retention timestamp.

## Feature Flags

- `ccsb.foundation.schema.1.0.0.1` gates use of the new managed schema package.
- `ccsb.runtime.projection.1.0.0` gates runtime consumption of projection payloads for schema contract `1.0.0`.
- `ccsb.nativeGraph.enabled` gates native graph board activation.

Feature flags remain off until managed import, backfill, compatibility validation, and count/hash checks pass.

## Rollback Limits

Metadata rollback is limited after a managed import. Do not delete imported schema components in production. Prefer behavior rollback: keep the prior active board version pointer, disable feature flags, continue using the previous projection schema version, and use publish snapshots or schedule-change rollback images through product APIs. Metadata repair is an additive forward managed solution.

## Rehearsal Evidence

A release rehearsal must capture:

- Static validator result.
- Live compatibility report.
- Managed package name and version.
- Managed import result.
- Backfill summary with counts and diagnostics.
- Pre/post counts and hashes for active board versions, runtime projections, publish snapshots/items, locks, schedule changes, operation audit, and outbox rows.
- Rollback drill result proving active boards and snapshots remain uncorrupted.