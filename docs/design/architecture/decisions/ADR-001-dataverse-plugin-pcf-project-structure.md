# ADR-001: Dataverse plug-in, early-bound, and PCF project structure

Date: 2026-07-10

## Status

Accepted

## Decision

The repository will use a layered Dynamics 365 / Dataverse structure:

- `src/Dataverse/EarlyBound` contains generated early-bound classes from `pac modelbuilder build`.
- `src/Shared` contains domain, application, Dataverse adapter, infrastructure, contract, and observability libraries.
- `src/Plugins/CCSB.Plugins` contains thin stateless Dataverse plug-in entry points.
- `src/CustomApis/CCSB.CustomApis` contains server-side Custom API handlers and contracts.
- `src/PCF/Controls` contains PCF controls, one folder per control.
- `src/PCF/Solutions` contains solution-packaging projects for PCF controls.

## Tooling position

Use Microsoft Power Platform CLI as the default for new work:

- `pac modelbuilder build` for early-bound classes.
- `pac plugin init` / `pac plugin push` or Plug-in Registration Tool for plug-in package workflows.
- `pac pcf init` for PCF controls.
- `pac solution` commands for Dataverse solution packaging.

`spkl` is not the default for new development. It may be used only for legacy compatibility if a future task proves that an existing build or registration process depends on it.

## Rationale

Microsoft currently recommends `pac modelbuilder build` for Dataverse early-bound generation. The generated model is isolated so it can be regenerated safely and reviewed independently from hand-written plug-in or application code.

Plug-ins target .NET Framework 4.6.2 using SDK-style projects, matching Dataverse plug-in packaging requirements. Plug-in classes remain stateless and delegate behavior to shared application services.

PCF controls are generated with Power Platform CLI and kept separate from Dataverse server rules. PCF code may call versioned Custom APIs, but authoritative scheduling behavior stays in Dataverse services.
