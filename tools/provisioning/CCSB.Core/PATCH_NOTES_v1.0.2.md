# CCSB Core Generator — Patch Notes v1.0.2

## Fixed authentication guidance and fail-fast validation

- Corrected the .NET 8/MSAL interactive redirect requirement to `http://localhost`.
- Added connection-string validation to both `Build-CCSBCore.ps1` and `Program.cs`.
- The generator now stops before Dataverse sign-in when it receives an incompatible `app://...` redirect URI.
- Added `Start-CCSBInteractiveBuild.ps1`, which creates a loopback-safe OAuth connection string for interactive local use.
- Updated the template and README with the required Microsoft Entra configuration.
- No table manifest, table ownership, or solution-provisioning logic changed.

## Important

The `appid` parameter from a Dynamics model-driven app URL is not a Microsoft Entra Application (client) ID.
