# Deployment

- `pipelines/`: promotion pipelines and approval gates.
- `scripts/`: idempotent install, upgrade, data, smoke-test, and rollback helpers.
- `settings/`: non-secret deployment settings templates.

Promote the same managed artefacts through Dev, Test, UAT, and Production. Production requires approvals, clean-environment import evidence, backup/rollback readiness, and post-deployment verification.

