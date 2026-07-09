# CCSB Foundation Schema Provisioner v1.0.0.3 — Validation Record

## Static validation completed

- Schema manifest parsed successfully.
- Confirmed 14 declared new foundation tables.
- Confirmed 52 declared lookup relationships.
- Confirmed 228 new-table business fields and 8 extensions are unchanged from the v1.0.0.2 schema manifest.
- Added C# interactive OAuth command-line inputs:
  - `--environment-url`
  - `--username`
  - `--app-id`
  - `--redirect-uri`
  - `--token-cache-store-path`
- Added `Start-CCSBInteractiveSchemaBuild.ps1` with the requested `-EnvironmentUrl` and `-Username` interface.
- Replaced the invalid legacy `app://...` redirect in executable code with `http://localhost`.
- Confirmed explicit `--environment-url` takes precedence over any existing `DATAVERSE_CONNECTION_STRING` environment variable.
- Confirmed the interactive path does not accept or store a password.
- Retained `-WhatIf` as a connection-free validation path.

## Limitation

No live Dataverse sign-in or metadata provisioning run was possible in this packaging environment because it requires a target tenant, an interactive browser session, and Dataverse privileges. The package should be validated with `-WhatIf` locally, then run against DEV using the interactive launcher.
