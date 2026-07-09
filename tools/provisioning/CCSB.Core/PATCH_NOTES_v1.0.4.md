# CCSB Core Generator — Patch Notes v1.0.4

## Fixed interactive login on Windows profiles that cannot map their SID

### Error addressed

```text
MSAL ErrorCode: get_user_name_failed
Win32Exception (1332): No mapping between account names and security IDs was done.
```

### Root cause

The v1.0.3 interactive helper included `Integrated Security=true`. The Dataverse SDK interprets this as a request to use the current Windows identity. On the reported Windows profile, the account SID cannot be resolved to an account name, so authentication fails before the browser-based Microsoft Entra sign-in flow begins.

### Correction

- Removed `Integrated Security=true` from `Start-CCSBInteractiveBuild.ps1`.
- Added `Run-CCSBInteractiveValidation.ps1` for a clear validation-only invocation.
- Added a fail-fast guard to `Build-CCSBCore.ps1` for accidental use of `Integrated Security=true`.
- Kept `RedirectUri=http://localhost`, `Username=<Microsoft 365 UPN>`, and `LoginPrompt=Always`.
- No C# provisioning logic, 26-table manifest, or solution-export behaviour changed.

## Use

```powershell
.\Start-CCSBInteractiveBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab8.crm.dynamics.com" `
  -Username "your.name@yourtenant.com"
```
