# US-002-T01 - Product and Schema Compatibility Contract

**Status:** Implemented contract artifact and static validation  
**Task:** Define product and schema compatibility contract  
**Contract:** `docs/design/api-contracts/compatibility/US-002-T01-compatibility-contract.json`

## Contract Boundary

CCSB V1 uses one explicit compatibility line:

| Dimension | V1 value | Rule |
|---|---:|---|
| Product semantic version | `1.0.0` | Same major version only; downgrade activation is blocked. |
| Foundation solution version | `1.0.0.1` | Must match the managed schema package used by release validation. |
| Configuration schema version | `1.0.0` | Board activation only supports configured schema versions listed in the contract. |
| Runtime projection schema version | `1.0.0` | Current projections must match or be regenerated before runtime use. |

## Activation Consumption

`ccsb_ValidateBoardVersion` and `ccsb_ActivateBoardVersion` must load the JSON contract, compare product/schema/projection versions, and write `ccsb_configurationvalidationresult` records with stable `CCSB-COMPAT-*` codes. Activation is fail-closed when product version, schema version, projection version, migration state, feature flag, or live schema validation evidence is unsupported or missing.

Current persistence uses existing fields: `ccsb_boardversion` version/hash/validation fields, `ccsb_runtimeprojection.ccsb_projectionschemaversion`, projection status/hash/token fields, and validation-result evidence fields. Explicit product version, configuration schema version, and migration-state columns remain the next task under `US-002-T02`.

## Supported Paths

| Path | From | To | Activation result |
|---|---|---|---|
| Initial V1 install | No prior CCSB contract | Product `1.0.0`, schema `1.0.0`, projection `1.0.0` | Allowed after schema validation. |
| V1 managed patch | Product `1.0.0`, schema `1.0.0`, projection `1.0.0` | Foundation solution `1.0.0.1` | Allowed with feature flags and zero blockers. |

Unsupported paths include product major mismatch, schema major mismatch, stale projection, pending/failed migration, missing compatibility report, and any downgrade.

## Done Evidence

- Versioned JSON contract created.
- Static validator checks contract syntax, supported paths, diagnostic codes, Custom API consumers, and schema field bindings.
- Generated report: `docs/implementation/testing/evidence/US-002-T01/static-report.md`.
