# Import and Migration Order

This order supports US-004-T10 managed schema upgrade rehearsal for CCSB Foundation Schema source build `1.0.0.6`, Dataverse solution `ccsb_foundationschema` version `1.0.0.1`, and schema contract `1.0.0`.

## DEV Source Build

1. Import or keep the existing `CCSB_Core` unmanaged solution.
2. Import or keep the existing `CCSB_CoreSchema` unmanaged extension solution.
3. Run this provisioner against DEV to create or repair the unmanaged `ccsb_foundationschema` solution.
4. Run live metadata compatibility validation and write `out\foundation-schema-compatibility.json`.
5. Publish customizations.
6. Export packages from DEV:
   - `CCSB_FoundationSchema_1_0_0_1_unmanaged.zip` for DEV repair evidence only.
   - `CCSB_FoundationSchema_1_0_0_1_managed.zip` with `-ExportManaged` for TEST/UAT/production rehearsal.

## TEST, UAT, and Production-Like Managed Upgrade

1. Confirm environment backup/restore or platform recovery point is available.
2. Confirm `CCSB_Core` and `CCSB_CoreSchema` are already present at compatible versions.
3. Import `CCSB_FoundationSchema_1_0_0_1_managed.zip` through the Dataverse managed solution upgrade path.
4. Keep schema/runtime feature flags off after import.
5. Capture pre-backfill counts and hashes for active board versions, runtime projections, publish snapshots/items, publish locks, schedule changes, operation audit, and outbox rows.
6. Run controlled, idempotent backfill:
   - Create a `ccsb_boardregistry` for each approved operational board when missing.
   - Create one draft `ccsb_boardversion` from existing board configuration, views, groups, status definitions, resource definitions, event type definitions, and rules.
   - Validate mappings and activate only through the lifecycle process.
   - Link the operational Schedule Board to the Board Registry and active Board Version.
   - Link existing schedule versions and publish snapshots where historical evidence exists.
7. Run compatibility validation again and confirm no blocking diagnostics.
8. Enable feature flags in order only after validation and backfill pass.
9. Run rollback drill by disabling flags and proving the prior active board/projection path remains readable.
10. Capture post-upgrade counts and hashes and confirm protected evidence records are unchanged except for append-only audit/backfill evidence.

Do not create a second Board Version for the same active configuration until migration validation is complete. Do not import unmanaged solution layers into TEST, UAT, or production to repair a managed upgrade. Read `Schema_Migration_and_Upgrade_Policy.md` before running a managed import rehearsal.