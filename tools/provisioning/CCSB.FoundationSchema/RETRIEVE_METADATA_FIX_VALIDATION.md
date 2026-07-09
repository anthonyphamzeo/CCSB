# v1.0.0.4 validation record

Validated locally:

- `Program.cs` imports `Microsoft.Xrm.Sdk.Messages`.
- No generic `OrganizationRequest("RetrieveEntity")` remains.
- No generic `OrganizationRequest("RetrieveAttribute")` remains.
- Create/retrieve/publish/export metadata operations use typed SDK request classes.
- The package preserves the 14-table foundation schema manifest unchanged.
- The ZIP includes all build scripts, schema manifest, docs, and the repair note.

A live execution cannot be performed here because it requires the target Dataverse environment and interactive Entra authentication.
