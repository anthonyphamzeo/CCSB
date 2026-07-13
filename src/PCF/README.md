# PCF Components

## Controls

- `Planora.ConfigurationStudio`: governed authoring/orchestration experience for board configuration. It must not bypass lifecycle services or write authoritative configuration directly.
- `Planora.ScheduleBoardRuntime`: operational schedule workspace. It starts only from a compatible active projection and routes mutations through versioned Custom APIs.

## Shared

Only presentation concerns belong in `Shared/`: Fluent UI primitives, typed API clients/contracts, telemetry adapters, accessibility helpers, and test utilities. Server business rules must not be reimplemented in TypeScript.

Each control root should contain its generated PCF project files from `pac pcf init`. Hand-written implementation code belongs under `src/components`, `src/hooks`, `src/services`, `src/state`, `src/telemetry`, and `src/types`. Colocated PCF unit tests stay in the control `tests` folder, while cross-control UI suites live under `tests/UI/PCF`.

`Solutions/Planora.PCFControls` is reserved for the solution project that packages PCF controls for Dataverse import.
