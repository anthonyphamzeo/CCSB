# Shared Libraries

- `CCSB.Domain`: entities, value objects, policies, and domain errors; no Dataverse SDK dependency.
- `CCSB.Application`: use cases, ports, validation, authorization, idempotency, and transaction orchestration.
- `CCSB.Dataverse`: repositories, queries, execution-context adapters, and SDK extensions.
- `CCSB.Infrastructure`: configuration, messaging, persistence, clocks, IDs, and external adapters.
- `CCSB.Observability`: structured logging, metrics, traces, correlation, and redaction.
- `CCSB.Contracts`: stable cross-process event and API contract models.

Shared does not mean miscellaneous. A library needs a clear owner, dependency boundary, and independent tests.

