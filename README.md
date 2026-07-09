# CCSB / Planora Schedule Board

Enterprise Dynamics 365 and Dataverse implementation for the CCSB/Planora Schedule Board.

## Architecture rules

- Dataverse and server-side services are authoritative.
- PCF controls read governed, visible slices and perform mutations only through versioned Custom APIs.
- Plug-ins remain thin and delegate business rules to shared application services.
- Configuration uses environment variables and connection references; secrets never enter source control.
- Product components ship in managed solutions outside development.
- Every change is traceable to a task, design decision, test result, and release.

## Repository map

| Path | Purpose |
|---|---|
| `docs/` | Tracking documents, design artefacts, implementation records, and completed-work evidence |
| `tasks/` | Backlog, active work, completed tasks, and release-specific task lists |
| `src/` | PCF, plug-ins, Custom APIs, Dataverse solutions, shared libraries, and integrations |
| `tests/` | Unit, contract, integration, architecture, UI, accessibility, and performance tests |
| `build/` | CI definitions, reusable pipeline templates, and build scripts |
| `deploy/` | Environment-safe deployment configuration and release scripts |
| `config/` | Non-secret configuration contracts and per-environment templates |
| `tools/` | Validation, packaging, provisioning, and developer utilities |

See [docs/repository-structure.md](docs/repository-structure.md) for ownership and dependency guidance.

## Work item flow

1. Select or add an item in `tasks/backlog/`.
2. Move its task record to `tasks/in-progress/` on a `feature/<work-item>-<summary>` branch.
3. Keep schema, API, plug-in, and PCF changes separately reviewable.
4. Record validation and implementation evidence in `docs/implementation/`.
5. On acceptance, move the task record to `tasks/completed/` and update the release list.

