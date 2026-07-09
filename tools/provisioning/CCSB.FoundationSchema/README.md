# CCSB Foundation Schema Provisioner

This project creates the **CCSB Foundation Schema** in an unmanaged DEV Dataverse solution and can export either unmanaged DEV or managed release packages.

It provisions 14 foundation tables, their business fields, 52 Restrict lookup relationships, selected alternate keys, and migration-safe extensions to existing CCSB V1 Core tables. It uses supported Dataverse metadata messages, runs a fail-closed live metadata compatibility gate, and exports the resulting solution package from the connected DEV environment.

## v1.0.0.6 repair - verified Core entity resolution

Earlier source revisions incorrectly assumed that the table displayed in Power Apps as **Schedule Board** had logical name `ccsb_scheduleboard`. The screenshot confirms the display name only; it does not prove the logical name.

This revision resolves every existing Core dependency before any table, field, relationship, or key is changed. For the Schedule Board dependency it:

1. checks `ccsb_scheduleboard` exactly;
2. otherwise finds the unique custom table whose display name is **Schedule Board**;
3. uses the discovered logical name for the two Schedule Board fields and both related lookup relationships.

If the Core Schedule Board resolves to `ccsb_board`, that is supported. The foundation board identity table is now `ccsb_boardregistry`, and the Core Schedule Board registry lookup is `ccsb_boardregistryid` so it does not collide with the Core table primary key.

When automatic discovery is ambiguous, pass the actual value shown in the table **Logical name** property:

```powershell
-CoreEntityOverride 'ccsb_scheduleboard=<actual-logical-name>'
```

Read `CORE_ENTITY_RESOLUTION_FIX.md` for the full repair rationale.

## Prerequisites

- .NET 8 SDK.
- Permissions to create tables, columns, relationships, entity keys, solutions, publish customizations, and export solutions in the DEV Dataverse environment.
- Existing `CCSB_Core` and `CCSB_CoreSchema` solutions already imported into DEV.

## Validate locally

```powershell
.\run-provisioner.ps1 -WhatIf
```

This validates the declarative JSON only. It does not connect to Dataverse.

## Validate live metadata without changes

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com" `
  -ValidateLiveOnly `
  -CompatibilityReportPath "out\foundation-schema-compatibility.json"
```

The connected compatibility gate checks the live solution version, table ownership, required fields, field types, field constraints, choice values, lookup targets, relationship cardinality, and Restrict delete behavior. Any mismatch is reported with table/field/relationship diagnostics and blocks publish/export.

## Run interactively in DEV

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com"
```

If the console reports ambiguous Schedule Board tables, inspect the **Logical name** in Power Apps and rerun with the explicit override:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com" `
  -CoreEntityOverride "ccsb_scheduleboard=<actual-logical-name>"
```

The default unmanaged DEV export location is:

```text
out\CCSB_FoundationSchema_1_0_0_1_unmanaged.zip
```

## Managed upgrade rehearsal export

Use `-ExportManaged` after live compatibility validation when preparing TEST, UAT, or production rehearsal packages:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org.crm.dynamics.com" `
  -Username "user@tenant.onmicrosoft.com" `
  -ExportManaged `
  -CompatibilityReportPath "out\foundation-schema-compatibility.json"
```

The default managed export location is:

```text
out\CCSB_FoundationSchema_1_0_0_1_managed.zip
```

Read `docs/Schema_Migration_and_Upgrade_Policy.md` before importing the managed package into any non-DEV environment.

## Safe retry after a partial run

Keep the existing unmanaged solution `ccsb_foundationschema` in DEV. Re-running the provisioner finds existing tables, fields, lookup columns, and alternate keys and adds only the missing components.

## Import order

1. `CCSB_Core`.
2. `CCSB_CoreSchema`.
3. In DEV, use the exported `CCSB_FoundationSchema_1_0_0_1_unmanaged.zip` only for development-layer repair.
4. In TEST, UAT, and production rehearsal, use `CCSB_FoundationSchema_1_0_0_1_managed.zip` and keep feature flags off until validation and backfill pass.
5. Import the updated Model-Driven Apps solution only after the foundation solution is present.
