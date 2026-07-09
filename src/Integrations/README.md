# Integrations

- `AzureFunctions`: asynchronous compute and orchestration offloaded from Dataverse.
- `Messaging`: Service Bus/Event Grid publishers, consumers, retry, dead-letter, and outbox coordination.
- `Webhooks`: lightweight outbound adapters with authentication and replay protection.
- `Contracts`: integration-specific schemas and compatibility fixtures.

All integrations require managed identity or approved secret storage, bounded retries, idempotency, telemetry correlation, and a documented failure/recovery path.

