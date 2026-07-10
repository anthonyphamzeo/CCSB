# Planora.ConfigurationStudio PCF

Authoring and validation experience for board configuration.

## Generate the PCF shell

Run this from the control root when implementation begins:

```powershell
pac pcf init --namespace Planora --name ConfigurationStudio --template dataset --run-npm-install
```

After generation, keep implementation code organized under `src/`:

```text
src/
  components/    Reusable view components
  hooks/         PCF and state hooks
  services/      Custom API clients and adapters
  state/         View models and reducers
  telemetry/     Client-side telemetry adapters
  types/         UI-only TypeScript contracts
```

Rules:

- Use Custom APIs for authoritative mutations.
- Do not duplicate server-side configuration rules in TypeScript.
- Keep accessibility and keyboard navigation evidence with the related task.
