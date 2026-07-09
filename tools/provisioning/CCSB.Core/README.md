# CCSB Core Unmanaged Solution Generator v1.0.1

## Purpose

This package creates the **`CCSB_Core`** unmanaged Dataverse solution for the Custom Schedule Board product.

It creates exactly the following **26 custom tables** using the `ccsb_` publisher prefix:

- No business fields
- No Choice columns
- No lookup relationships
- No forms, views, apps, flows, plug-ins, or sample data
- Only the required **primary-name text column** (`ccsb_name`) on each table

The provisioning command then asks Dataverse to export the generated unmanaged solution ZIP. That exported ZIP is the real file to import into another Dynamics 365 / Dataverse environment.

> **Do not attempt to construct a Dataverse table solution ZIP by manually editing `customizations.xml`.**
> This package uses the supported Dataverse SDK metadata APIs to create the publisher, solution, and tables, and the Dataverse ExportSolution message to generate the importable archive.

---

## Solution identity

| Item | Value |
|---|---|
| Solution unique name | `CCSB_Core` |
| Solution display name | `CCSB Core` |
| Initial version | `1.0.0.0` |
| Publisher unique name | `CCSB` |
| Publisher prefix | `ccsb` |
| Publisher option value prefix | `81000` |
| Default language | English (LCID 1033) |
| Export output | `artifacts/CCSB_Core_1_0_0_0_unmanaged.zip` |

---


## Authentication fix for .NET 8 / MSAL

This provisioner is a `.NET 8` console application using the current Dataverse client and the MSAL system-browser flow. Its OAuth redirect URI must be an **HTTP loopback URI**.

Use:

```powershell
RedirectUri=http://localhost
```

Do **not** use:

```text
RedirectUri=app://58145B91-0C36-4500-8554-080854F2AC97
```

The latter is used by older .NET Framework/XRM Tooling examples but will fail in this package with the MSAL error `loopback_redirect_uri`.

### Fast interactive validation

```powershell
.\Start-CCSBInteractiveBuild.ps1 `
  -EnvironmentUrl "https://YOURORG.crm.dynamics.com" `
  -Username "your.name@yourtenant.com"
```

This uses Microsoft's development client ID for local validation and opens interactive sign-in. After validation completes, add `-Apply` to create the tables and export the unmanaged solution.

### Tenant-specific app registration

For repeatable team use, create a public client registration in the same Microsoft Entra tenant as the Dataverse environment:

1. Create an app registration named `CCSB Core Schema Provisioner`.
2. On **Authentication**, add `http://localhost` as the redirect URI for the desktop/mobile public-client application.
3. Under **API permissions**, add Dataverse delegated permission `user_impersonation`, then grant consent.
4. Use the **Application (client) ID** in the connection string `AppId` parameter.
5. Keep `RedirectUri=http://localhost` unchanged.

The `appid` in a Dynamics model-driven app URL is an AppModule ID; it is not an Entra application client ID and must not be used as `AppId`.


## Prerequisites

1. A **Dataverse development environment**. Do not build the base unmanaged solution in production.
2. The identity in the connection string must have **System Administrator** access. The Dataverse SDK table-creation operation also requires the related metadata, form, query, and customization privileges.
3. [.NET SDK 8](https://dotnet.microsoft.com/download/dotnet/8.0).
4. Internet access to restore the `Microsoft.PowerPlatform.Dataverse.Client` NuGet package.
5. Ensure no unrelated publisher already uses the `ccsb` customization prefix.

The first run creates a **publisher** named `CCSB` if no publisher uses the `ccsb` prefix. If a single compatible `ccsb` publisher already exists, the package uses it. If multiple publishers use that prefix, the package stops without applying changes.

---

## Important irreversible decisions

### Table ownership

Dataverse table ownership cannot be changed after a table is created. This package deliberately applies the following split:

- **Organization-owned:** product configuration, reusable calendars, reference data, hierarchy structures, schedule version, and publish snapshots.
- **User/team-owned:** operational records where future dispatcher, regional-team, or owner-based access controls can be useful.

The complete ownership register is in [`docs/Table-Ownership-Register.md`](docs/Table-Ownership-Register.md).

### Primary name field

Every table receives the only field required for initial creation:

| Property | Value |
|---|---|
| Logical name | `ccsb_name` |
| Schema name | `ccsb_Name` |
| Type | Single line of text |
| Format | Text |
| Maximum length | 200 |
| Required level | Optional / None |

Specific display labels are used, for example **Schedule Board Name**, **Resource Name**, and **Schedule Item Name**. The business field and relationship solution will be delivered later as an extension of `CCSB_Core`.

---

## Validate first — no changes

From the package root:

```powershell
.\Build-CCSBCore.ps1 `
  -ConnectionString "AuthType=OAuth;Username=YOUR-UPN;Integrated Security=true;Url=https://YOURORG.crm.dynamics.com;AppId=YOUR-ENTRA-CLIENT-ID;RedirectUri=http://localhost;LoginPrompt=Always;RequireNewInstance=true"
```

The command connects to Dataverse and reports:

- Whether a `ccsb` publisher already exists
- Whether `CCSB_Core` already exists
- Which requested tables already exist
- Whether existing tables have compatible ownership
- Which tables would be created

It does **not** create or change anything unless `-Apply` is supplied.

---

## Create and export the unmanaged solution

Run in the development environment only:

```powershell
.\Build-CCSBCore.ps1 `
  -ConnectionString "AuthType=OAuth;Username=YOUR-UPN;Integrated Security=true;Url=https://YOURORG.crm.dynamics.com;AppId=YOUR-ENTRA-CLIENT-ID;RedirectUri=http://localhost;LoginPrompt=Always;RequireNewInstance=true" `
  -Apply
```

Successful execution:

1. Creates or adopts the `CCSB` publisher.
2. Creates or adopts the unmanaged `CCSB_Core` solution.
3. Creates or adopts the 26 requested tables.
4. Publishes Dataverse customizations.
5. Exports the actual importable archive:

```text
artifacts\CCSB_Core_1_0_0_0_unmanaged.zip
```

6. Writes a build report:

```text
artifacts\CCSB_Core_build_report.json
```

---

## Import into another Dataverse environment

1. In the development environment, take the generated file:
   `artifacts\CCSB_Core_1_0_0_0_unmanaged.zip`
2. In the target environment, open **Solutions**.
3. Select **Import solution**.
4. Select the generated ZIP and import it.
5. Confirm that all 26 tables appear with the expected prefix and primary-name column.
6. Only after import has passed validation, import later CCSB schema-extension solutions for business fields, Choices, relationships, keys, forms, PCF controls, and apps.

Use a normal ALM path:

```text
Development (unmanaged) → Test/UAT (managed) → Production (managed)
```

The generated **unmanaged** ZIP is for development/reuse. Export a **managed** version from the approved development solution for Test/UAT/Production.

---

## Idempotent behaviour and recovery

The provisioner is safe to rerun:

- If a requested table does not exist, it is created.
- If it exists with matching ownership, it is added to `CCSB_Core` if needed.
- If it exists with different ownership, the run stops because ownership is immutable.
- If the solution/publisher already exists and is compatible, it is reused.
- The process is not a single transaction; if an unexpected error occurs, correct the issue and rerun. The report identifies completed work.

Do not delete and recreate a released table to fix a naming or ownership decision without first planning data migration and downstream dependency remediation.

---

## Package files

| File | Purpose |
|---|---|
| `table-manifest.json` | Authoritative 26-table plan: names, labels, descriptions, ownership, and categories |
| `src/CCSB.Core.Provisioner.csproj` | .NET 8 project |
| `src/Program.cs` | Dataverse SDK provisioner and solution exporter |
| `Build-CCSBCore.ps1` | PowerShell wrapper for validate and apply runs |
| `docs/Table-Ownership-Register.md` | Ownership rationale and exact table register |
| `docs/Import-Runbook.md` | Practical deployment and verification runbook |
| `docs/Microsoft-References.md` | Official Microsoft source links |
| `artifacts/` | Output directory for generated solution ZIP and build report |

---

## What comes next

Do not add business columns directly to the `CCSB_Core` base solution until the V1 field design has been approved.

The recommended next deliverable is a separate unmanaged extension solution, for example:

```text
CCSB_Schema
```

That solution should add the approved data model in layers:

1. Global Choices
2. Scalar fields
3. Lookup fields and relationships
4. Alternate keys
5. Table audit/change-tracking settings
6. Forms, views, model-driven app navigation, security roles, and PCF components

This separation keeps the foundational table decisions stable and makes upgrades safer.


## v1.0.1 correction

This revision fixes compilation against `Microsoft.PowerPlatform.Dataverse.Client` 1.2.10. Replace the original `src/Program.cs` with this version, or use the complete v1.0.1 package.


## v1.0.3 extraction note

This archive is intentionally flat. Create an empty target folder, then extract the ZIP **into** that folder. You should see these paths immediately:

```text
Build-CCSBCore.ps1
Start-CCSBInteractiveBuild.ps1
src\Program.cs
table-manifest.json
```

Do not run the scripts from a duplicated nested path such as:

```text
...\CCSB_Core_Unmanaged_Solution_Generator_v1_0_3\CCSB_Core_Unmanaged_Solution_Generator_v1_0_3\
```

## v1.0.4 authentication correction — do not use Integrated Security

The interactive helper no longer includes `Integrated Security=true`. That setting causes the Dataverse client to obtain the current Windows identity before interactive OAuth begins. It can fail with:

```text
MSAL ErrorCode: get_user_name_failed
Win32Exception (1332): No mapping between account names and security IDs was done.
```

Use browser-based OAuth with the Microsoft 365 user principal name instead:

```powershell
.\Start-CCSBInteractiveBuild.ps1 `
  -EnvironmentUrl "https://YOURORG.crm.dynamics.com" `
  -Username "your.name@yourtenant.com"
```

The connection string must **not** contain `Integrated Security=true`. `LoginPrompt=Always` forces the Microsoft sign-in experience.

For manual execution, use the included `Run-CCSBInteractiveValidation.ps1`.
