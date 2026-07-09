# Interactive Dataverse Authentication Fix — v1.0.0.3

## Cause of the failure

The previous guidance used the legacy `app://58145...` redirect URI. The provisioner targets .NET 8 and uses the Dataverse `ServiceClient`, which authenticates through MSAL. MSAL for modern .NET desktop/browser authentication accepts a loopback redirect URI, such as `http://localhost`, not the legacy `app://` redirect URI.

## New launcher

Use:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com"
```

`Username` is only a sign-in hint. The process opens a browser and supports MFA and Conditional Access. It does not collect, store, or send a password from PowerShell.

## App registration

For a DEV prototype, the launcher defaults to the Microsoft sample client ID documented for Dataverse OAuth examples. For production, create a tenant-owned Microsoft Entra public client app registration:

1. Register a single-tenant app in the same Entra tenant as the Dataverse environment.
2. Add the Mobile and desktop application redirect URI `http://localhost`.
3. Add Dataverse delegated permission `user_impersonation` and grant admin consent.
4. Pass the Application (client) ID through `-AppId`.
5. Ensure the interactive user has System Administrator or equivalent Dataverse metadata privileges for the initial schema build.

Example:

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com" `
  -AppId "00000000-0000-0000-0000-000000000000"
```

## Alternative automation authentication

For unattended CI/CD, use a confidential app registration and an application user with an appropriate Dataverse security role. Then pass a `ClientSecret` or certificate connection string to `run-provisioner.ps1 -ConnectionString`. Do not place secrets in source control.
