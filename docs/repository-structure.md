# Repository Structure and Ownership

## Dependency direction

```text
PCF controls -> typed client contracts -> versioned Custom APIs
Plugin steps -> application services -> domain
Custom API handlers -> application services -> Dataverse/infrastructure adapters
Integrations -> application contracts -> messaging/Dataverse adapters
```

Dependencies point inward toward `CCSB.Domain` and `CCSB.Application`. UI, Dataverse SDK, telemetry, and messaging concerns must not leak into the domain layer.

## Solution boundaries

- `CCSB.Core`: publisher, shared schema, configuration, security primitives, environment variables, and common server components.
- `CCSB.Scheduling`: scheduling tables, Custom APIs, plug-in assemblies, operational services, audit, publish, and rollback components.
- `CCSB.ModelDrivenUX`: model-driven app, forms, views, command definitions, web resources, and both PCF controls.

Introduce another solution only when it has a distinct lifecycle and dependency boundary. Avoid circular solution dependencies.

## Naming

- Dataverse publisher prefix: `ccsb`.
- .NET namespaces: `CCSB.<Layer>[.<Feature>]`.
- PCF control namespaces: `Planora.ConfigurationStudio` and `Planora.ScheduleBoardRuntime`.
- Work item branches: `feature/US-###-T##-short-description`.
- Releases: semantic versioning, with release records under `tasks/releases/`.

## Generated content

Unpacked Dataverse solution source belongs in each solution's `src/` directory. Packed ZIPs, build output, NuGet/npm caches, credentials, and environment-specific secrets are never committed.

