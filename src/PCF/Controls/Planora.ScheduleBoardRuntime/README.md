# Planora.ScheduleBoardRuntime PCF

Runtime scheduling workspace for dispatchers, planners, and field operations.

## Generate the PCF shell

Run this from the control root when implementation begins:

```powershell
pac pcf init --namespace Planora --name ScheduleBoardRuntime --template dataset --run-npm-install
```

After generation, keep implementation code organized under `src/`:

```text
src/
  components/    Timeline, swimlane, card, conflict, and command components
  hooks/         PCF lifecycle and data loading hooks
  services/      Custom API clients and Dataverse read adapters
  state/         Runtime board state and command queues
  telemetry/     Client-side telemetry adapters
  types/         UI-only TypeScript contracts
```

Rules:

- Start from a compatible active runtime projection.
- Treat Dataverse and Custom APIs as authoritative.
- Keep virtualization, performance, and accessibility tests with each scheduling task.
