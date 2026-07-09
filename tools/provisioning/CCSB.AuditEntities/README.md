# CSB Audit Entities Provisioner

Console app for provisioning the optimized CCSB audit/control entity set into Dataverse.

It creates or updates an unmanaged solution named **CSB Audit Entities** (`CSB_AuditEntities`) with publisher prefix `ccsb`, then provisions:

- 6 custom tables
- 133 simple custom fields
- 46 lookup relationships
- 6 primary name fields and 6 Dataverse primary IDs
- 6 main forms
- 12 public system views
- 6 alternate keys

The full manifest is in [schema/csb.auditentities.schema.json](schema/csb.auditentities.schema.json). It is generated from the approved optimized design using [tools/build_manifest_from_optimized_design.py](tools/build_manifest_from_optimized_design.py).

## Safety Behavior

The provisioner is intentionally idempotent where Dataverse supports it:

- Existing matching tables are reused.
- Missing fields, relationships, keys, forms, and views are created.
- Existing generated forms and views are updated.
- Existing tables with the wrong ownership fail fast.

Ownership is the non-negotiable guardrail. Dataverse table ownership cannot be changed after table creation, so the app stops if, for example, `ccsb_schedulechange` already exists as `UserOwned` when the optimized design requires `OrganizationOwned`.

## What-If Validation

Run this first. It does not connect to Dataverse.

```powershell
.\run-provisioner.ps1 -WhatIf
```

Expected summary:

```text
Tables: 6; simple fields: 133; lookup relationships: 46; expected total columns including primary id/name: 191; forms: 6; views: 12.
```

## Provision org314f8ab8

Interactive browser sign-in:

```powershell
.\run-provisioner.ps1 -EnvironmentUrl "https://org314f8ab8.crm.dynamics.com" -Username "user@tenant.onmicrosoft.com"
```

Using a Dataverse connection string:

```powershell
.\run-provisioner.ps1 -Connection "AuthType=ClientSecret;Url=https://org314f8ab8.crm.dynamics.com;ClientId=...;ClientSecret=...;TenantId=..."
```

To create metadata without exporting the unmanaged solution zip:

```powershell
.\run-provisioner.ps1 -EnvironmentUrl "https://org314f8ab8.crm.dynamics.com" -SkipExport
```

If the target environment does not yet contain all CCSB core/foundation tables, a full run will fail on missing lookup targets. For a partial table/field pass:

```powershell
.\run-provisioner.ps1 -EnvironmentUrl "https://org314f8ab8.crm.dynamics.com" -SkipMissingRelationshipTargets
```

Use the partial mode only during build-out. A production-ready run should create all 46 relationships.
