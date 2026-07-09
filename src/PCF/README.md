# PCF Components

## Controls

- `Planora.ConfigurationStudio`: governed authoring/orchestration experience for board configuration. It must not bypass lifecycle services or write authoritative configuration directly.
- `Planora.ScheduleBoardRuntime`: operational schedule workspace. It starts only from a compatible active projection and routes mutations through versioned Custom APIs.

## Shared

Only presentation concerns belong in `Shared/`: Fluent UI primitives, typed API clients/contracts, telemetry adapters, accessibility helpers, and test utilities. Server business rules must not be reimplemented in TypeScript.

Each control should contain its manifest, generated PCF project files, `components`, `hooks`, `services`, `state`, `types`, and colocated unit tests.

