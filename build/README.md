# Build and Continuous Integration

- `pipelines/`: CI entry points for restore, lint, build, test, security/licence checks, solution pack/unpack verification, and artefact publication.
- `templates/`: reusable pipeline jobs and steps.
- `scripts/`: cross-platform or PowerShell build utilities.

Pipelines must pin tool/dependency versions, generate an SBOM, fail on incompatible solution/API/schema changes, and never emit secrets.

