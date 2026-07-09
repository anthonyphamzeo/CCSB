# Technical Source

The source tree separates platform packaging, presentation, server execution, business logic, and external integration.

| Area | Responsibility |
|---|---|
| `Dataverse/` | Unpacked solutions, configuration schema, security, reference/migration data |
| `PCF/` | Configuration Studio and Schedule Board Runtime controls plus UI-only shared code |
| `Plugins/` | Dataverse event steps and thin execution adapters |
| `CustomApis/` | Versioned request/response contracts and server-authoritative handlers |
| `Shared/` | Domain, application, Dataverse, infrastructure, and observability libraries |
| `Integrations/` | Azure Functions, messaging, webhooks, and integration contracts |
| `Automation/` | Governed cloud flows and custom connectors |
| `ClientExtensions/` | Model-driven JavaScript and other web resources |

