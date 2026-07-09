# CCSB Core Generator v1.0.1 — Build Fix

## Fixed compiler errors

1. `AppContext` ambiguity
   - `AppContext.BaseDirectory` is now `global::System.AppContext.BaseDirectory`.

2. Missing `CreateSolutionRequest`
   - `CreateSolutionRequest` is not available from `Microsoft.PowerPlatform.Dataverse.Client` 1.2.10.
   - The provisioner now creates the Dataverse `solution` table row using the standard `IOrganizationService.Create` method.

3. `EntityComponentType` out of scope
   - The table component type constant (`1`) is now defined in `CoreSolutionProvisioner`, which uses it.

4. SDK message namespace isolation
   - Solution operations now use the `CrmMessages` alias for `Microsoft.Crm.Sdk.Messages`.

## What to do

Use the complete v1.0.1 package. From its root folder run:

```powershell
.\Build-CCSBCore.ps1 `
  -ConnectionString "AuthType=OAuth;Url=https://YOURORG.crm.dynamics.com;AppId=YOUR-APP-ID;RedirectUri=http://localhost;LoginPrompt=Auto" `
  -Apply
```

The created importable file is:

```text
artifacts\CCSB_Core_1_0_0_0_unmanaged.zip
```
