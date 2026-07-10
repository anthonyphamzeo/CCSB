# Shared Libraries

Shared libraries contain reusable code that is safe to reference from plug-ins, Custom APIs, integration workers, tests, and provisioning tools.

| Project | Purpose |
|---|---|
| `CCSB.Domain` | Pure domain entities, value objects, and policies |
| `CCSB.Contracts` | Versioned DTOs, Custom API contracts, and event contracts |
| `CCSB.Application` | Use-case orchestration and application services |
| `CCSB.Dataverse` | Dataverse repositories, queries, and mappings |
| `CCSB.Infrastructure` | Sandbox-safe infrastructure adapters |
| `CCSB.Observability` | Tracing, telemetry, and correlation helpers |

Dependencies must point inward:

`Presentation/Plugin adapters -> Application -> Domain`

`Application -> Contracts/Abstractions`

Do not create direct dependencies from domain logic to Dataverse SDKs, PCF, Azure SDKs, or generated UI contracts.
