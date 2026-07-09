# Package Validation Report

Generated: 2026-06-24
Table manifest SHA-256: `d4b8b9a7349771568ebd4ace87bb328e1bf1c562b45c1efe2be377ad034131f9`

## Static checks completed

- [x] **Approved table count** — 26 requested table definitions are present.
- [x] **Approved table names** — The manifest contains exactly the 26 table logical names supplied by the user.
- [x] **Publisher prefix** — Every table logical name uses the ccsb_ prefix; publisher prefix is ccsb.
- [x] **Primary column** — Every table will receive only the required primary-name text field ccsb_name (schema ccsb_Name, length 200).
- [x] **Ownership split** — 17 organization-owned and 9 user/team-owned tables are declared.
- [x] **SDK usage** — Provisioner uses a standard Create operation on the Dataverse solution table, CreateEntityRequest, AddSolutionComponentRequest, PublishAllXmlRequest and ExportSolutionRequest.
- [x] **Idempotency safeguards** — Provisioner validates publisher/solution/table state, adopts compatible existing tables, and stops for incompatible ownership.

## Execution limitation

This workspace does not have a .NET SDK, PAC CLI, or authenticated Dataverse environment. The C# provisioner has therefore **not** been compiled or executed against Dataverse here.

The package is designed to generate the actual importable unmanaged solution ZIP only after the supported Dataverse SDK calls create the tables in a development environment and the Dataverse ExportSolution message exports that real solution. Run validation-only mode first, then run with `-Apply`.

## Scope verification

The package creates the 26 requested tables plus the required primary-name text column on each table. It intentionally does not create the later business fields, global Choices, local Choices, alternate keys, relationships, forms, views, model-driven apps, PCF controls, flows, plug-ins, or data.

## v1.0.1 Build Correction

- Resolves `AppContext` ambiguity by explicitly using `global::System.AppContext`.
- Replaces the unavailable `CreateSolutionRequest` with a supported standard create operation for the Dataverse `solution` table.
- Places the entity solution-component type constant in `CoreSolutionProvisioner`, where it is used.
- Uses an explicit `Microsoft.Crm.Sdk.Messages` alias for solution export, publish and add-component SDK messages.
