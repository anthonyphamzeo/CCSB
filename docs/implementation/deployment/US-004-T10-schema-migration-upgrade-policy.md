# US-004-T10 - Schema Migration and Upgrade Policy

**Status:** Implemented policy, tooling hook, and static rehearsal contract  
**Task:** Deliver schema migration and upgrade policy  
**Package scope:** CCSB Foundation Schema source build `1.0.0.6`, Dataverse solution `ccsb_foundationschema` version `1.0.0.1`, schema contract `1.0.0`

## Implementation Summary

US-004-T10 defines the supported path for moving the CCSB foundation schema through managed Dataverse solution upgrades without corrupting active board configuration, runtime projections, schedule versions, publish snapshots, locks, audit records, or outbox evidence.

The latest Foundation Schema package remains an unmanaged DEV provisioning source, because Dataverse metadata must be created and repaired in a development layer. The provisioner now also supports a controlled managed export using `-ExportManaged` / `--export-managed`, producing `CCSB_FoundationSchema_1_0_0_1_managed.zip` after live compatibility validation and publish. TEST, UAT, and production imports must use the managed package, not the unmanaged DEV source.

The policy is additive-first. A schema upgrade may add tables, optional columns, choice options, Restrict lookup relationships, alternate keys, validation result fields, and non-blocking compatibility checks. A release may only tighten requiredness or runtime behavior after an idempotent backfill has completed, compatibility validation has passed, and the feature flag for the consuming runtime path has been enabled in a controlled environment.

## Additive Migration Rules

| Area | Allowed rule | Required evidence |
|---|---|---|
| Tables | Add new `ccsb_*` tables with stable logical names, organization/user ownership chosen before release, and no overlap with Core table logical names. | Static schema validation and live metadata compatibility report. |
| Fields | Add optional fields first. Required fields must have a default/backfill plan and stay non-blocking for at least one compatibility period. | Backfill result count, null-count check, and validation result records. |
| Choices | Append new option values only. Never reuse, renumber, or relabel an option in a way that changes meaning. | Choice diff in release notes and validator pass. |
| Relationships | Add lookup relationships with Delete Restrict. Required lookup enforcement must follow data backfill. | Relationship cardinality and cascade diagnostics from the live gate. |
| Keys | Add alternate keys before runtime code depends on them. Resolve duplicates before enabling write paths. | Key conflict report and seed/integrity test pass. |
| Runtime projections | Add new projection schema versions side by side. Keep prior projection versions readable during the compatibility period. | Projection compatibility validation and stale-projection negative test. |
| Validation | Add diagnostics as non-blocking first, then promote to blocking after compatibility evidence exists. | `CCSB-SCHEMA-*` and configuration validation evidence. |

## Destructive Change Prohibition

The following changes are not supported in a managed upgrade package:

- Delete, rename, or repurpose any released table, field, relationship, alternate key, choice value, or logical name.
- Change field type, reduce max length, reduce numeric range, reduce precision, or change date behavior for released columns.
- Convert an optional field or lookup to required before all existing records are backfilled and validated.
- Change relationship delete behavior away from Restrict for board, board-version, projection, publish, lock, audit, schedule-change, or outbox records.
- Mutate active or retired `ccsb_boardversion` records, publish snapshots, snapshot items, operation audit rows, outbox events, or rollback images as part of schema import.
- Remove historical projections or snapshots to make a new schema validate.
- Import unmanaged solution layers into TEST, UAT, or production to repair a managed schema issue.

If a breaking change is unavoidable, it must be delivered as a new major compatibility line with a new side-by-side table/field or projection version, a migration bridge, explicit deprecation period, and customer-facing release notes.

## Data Backfill Policy

Backfills run after managed solution import and before feature activation. They must be idempotent, scoped, observable, and reversible at the data-behavior level.

| Backfill rule | Policy |
|---|---|
| Scope | Filter by board registry, board version, schedule version, projection version, or source record key. Never scan or mutate unrelated customer records. |
| Defaults | Use deterministic defaults from the policy manifest, existing configuration, or tenant-approved release settings. Do not infer scheduling semantics silently. |
| Active boards | Active board versions remain immutable. If normalized configuration must change, clone to Draft, validate, then activate through the lifecycle API. |
| Publish evidence | Publish snapshots, snapshot items, operation audit, locks, schedule changes, and outbox rows are append-only. Backfill may add missing evidence fields but must not rewrite historical meaning. |
| Auditing | Every data migration run creates operation/audit evidence with correlation ID, package version, counts, result, and retention timestamp. |
| Failure handling | Failed backfill leaves feature flags off, writes validation diagnostics, and is safe to rerun after remediation. |

## Feature Flags and Compatibility Periods

Schema import alone must not enable new runtime behavior. The release uses three gates:

1. `ccsb.foundation.schema.1.0.0.1` - confirms the managed schema package and live compatibility report are present.
2. `ccsb.runtime.projection.1.0.0` - allows runtime consumers to use projection payloads that match schema contract `1.0.0`.
3. `ccsb.nativeGraph.enabled` - enables native schedule graph usage only after the target board version validates in native mode.

Minimum compatibility period is 90 days for any minor schema upgrade. During that period, previously active board versions and current runtime projections remain readable, runtime code must fail closed on unsupported schema versions, and new validation rules run in observe or warning mode unless they protect data integrity.

## Rollback Limits

Managed Dataverse schema import is not treated as a normal data rollback boundary. Once metadata is imported successfully, rollback means disabling new behavior and moving forward with an additive repair package, not deleting schema components.

Supported rollback actions:

- Keep or restore the prior active board version pointer when activation has not completed.
- Disable feature flags and force runtime to use the previous projection schema version.
- Use publish snapshots and schedule-change rollback images to reverse operational schedule changes through product APIs.
- Re-run idempotent backfill after fixing validation failures.
- Import an additive hotfix managed solution if metadata repair is required.

Unsupported rollback actions:

- Delete newly imported managed tables or fields in production as a rollback mechanism.
- Rewrite publish snapshot payloads, operation audit rows, outbox events, or immutable active board-version records.
- Downgrade runtime code while leaving feature flags enabled for a newer schema contract.

## Managed Upgrade Rehearsal

Acceptance for US-004-T10 is met when this rehearsal passes in a non-production environment:

1. Run static schema validation and the T10 static policy validator.
2. Run connected live metadata validation with `-ValidateLiveOnly` and write a compatibility report.
3. Export the managed package from DEV using `-ExportManaged` after publish.
4. Import the managed package into TEST using the platform solution upgrade path.
5. Seed or retain the deterministic T09 dataset and record pre-upgrade counts and hashes for active board versions, projections, snapshots, audit, outbox, locks, and schedule changes.
6. Run idempotent backfill with feature flags off.
7. Run compatibility validation again and confirm no blocking diagnostics.
8. Enable feature flags in order and validate mapped and native graph board modes.
9. Run rollback drill by disabling flags and confirming the prior active board version, projections, snapshots, and audit evidence remain readable and unmodified.
10. Capture release evidence: managed package name/version, compatibility report, backfill summary, validation report, count/hash comparison, and rollback drill result.

## Boundary

This task delivers policy, managed export support, local static validation, and an upgrade rehearsal contract. Live Dataverse import, customer-specific backfill execution, environment backup/restore, and production approval remain release-management activities outside this local workspace.