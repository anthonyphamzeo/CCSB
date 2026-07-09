# v1.0.0.2: `-WhatIf` and connection setup fix

## What was corrected

The previous wrapper was an advanced PowerShell script and used a parameter named
`WhatIf`. In some Windows PowerShell invocation contexts, `-WhatIf` can be treated
as a PowerShell common parameter instead of the provisioner's own validation switch.
That meant the wrapper did not forward `--what-if` to `Program.cs`, so the provisioner
continued to its connection check.

This release intentionally uses a normal parameterized PowerShell script and builds
native `dotnet` arguments explicitly. Both of these commands now execute validation
without requiring a Dataverse connection:

```powershell
.\run-provisioner.ps1 -WhatIf
# Equivalent explicit name:
.\run-provisioner.ps1 -ValidateOnly
```

Expected result:

```text
Validation mode: the provisioner will not connect to Dataverse or make metadata changes.
Schema: ccsb_foundationschema v1.0.0.0
New tables: 14; new-table fields: 228; relationships: 52; existing-table fields: 8.
What-if complete. No Dataverse metadata was changed.
```

## Provisioning requires a Dataverse connection

The actual create/update/export operation needs a Dataverse connection. This is by
design: schema metadata can only be created in a target Dataverse environment.

At the PowerShell script layer, use `-ConnectionString`, not the internal .NET
`--connection` argument.

### Interactive OAuth for development

```powershell
$connection = 'AuthType=OAuth;Url=https://YOURORG.crm.dynamics.com;AppId=<ENTRA_APP_CLIENT_ID>;RedirectUri=http://localhost;LoginPrompt=Auto'
.\run-provisioner.ps1 -ConnectionString $connection
```

### Service principal for unattended DEV/CI use

```powershell
$env:DATAVERSE_CONNECTION_STRING = 'AuthType=ClientSecret;Url=https://YOURORG.crm.dynamics.com;ClientId=<ENTRA_APP_CLIENT_ID>;ClientSecret=<CLIENT_SECRET_VALUE>'
.\run-provisioner.ps1
```

The identity must be registered as a Dataverse application user and have sufficient
permissions in DEV to create solution components, publish customizations, and export
an unmanaged solution. For the first controlled DEV run, System Administrator is the
simplest role; least-privilege permissions can be designed after the schema is stable.

Do not store the client secret in source control, the JSON schema, README files, or a
PowerShell profile. Prefer a secure secret store or pipeline secret variable.
