# Contributing

## Branch and task discipline

- Start from an accepted task record and use `feature/US-###-T##-short-description`.
- Move the record to `tasks/in-progress/` and identify the owner, release, and validation plan.
- Keep schema, server contract, PCF, and deployment changes independently reviewable.
- Use the pull request template and obtain CODEOWNER review.

## Quality gates

Changes must preserve dependency direction, use supported Dynamics 365/Power Platform APIs, include proportionate automated tests, and document security, telemetry, performance, accessibility, deployment, and rollback impacts.

Generated packages, credentials, production data, build output, and local IDE state are prohibited.

## Completion

After acceptance, move the task record to `tasks/completed/`, link durable evidence under `docs/implementation/testing/evidence/`, and update the target release record.

