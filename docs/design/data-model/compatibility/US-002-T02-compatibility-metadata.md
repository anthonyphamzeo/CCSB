# US-002-T02 - Compatibility Metadata

**Status:** Implemented schema metadata and static validation  
**Task:** Add compatibility metadata  
**Contract:** `docs/design/data-model/compatibility/US-002-T02-compatibility-metadata.json`

## Implementation Summary

US-002-T02 adds explicit compatibility metadata to the foundation schema so board activation and runtime bootstrap no longer infer compatibility from labels, hashes, or package context alone.

The schema now persists product and configuration schema versions on `ccsb_boardversion`, alongside migration state and compatibility status. `ccsb_runtimeprojection` now carries the product and configuration schema versions used to generate the projection in addition to the existing projection schema version.

The new columns are additive and migration-safe at Dataverse metadata level. Activation and runtime validation must enforce non-null values for active board versions and current projections after backfill.

## Field Bindings

| Entity | Field | Type | Metadata required | Runtime invariant |
|---|---|---:|---:|---|
| `ccsb_boardversion` | `ccsb_productversion` | String | No | Required when lifecycle is Active. |
| `ccsb_boardversion` | `ccsb_configurationschemaversion` | String | No | Required when lifecycle is Active. |
| `ccsb_boardversion` | `ccsb_migrationstate` | Choice | No | Active versions allow only None or Completed. |
| `ccsb_boardversion` | `ccsb_compatibilitystatus` | Choice | No | Active versions allow only Compatible or Compatible With Warnings. |
| `ccsb_runtimeprojection` | `ccsb_productversion` | String | No | Required when projection is current. |
| `ccsb_runtimeprojection` | `ccsb_configurationschemaversion` | String | No | Required when projection is current. |
| `ccsb_runtimeprojection` | `ccsb_projectionschemaversion` | String | Yes | Existing required projection contract stamp. |

## Active Board Version Invariant

Every active board version must report unambiguous compatibility metadata: product version, configuration schema version, migration state, compatibility status, configuration hash, and validation status. Missing metadata emits `CCSB-COMPAT-METADATA-MISSING` and blocks activation.

## Current Projection Invariant

Every current runtime projection must report product version, configuration schema version, projection schema version, content hash, and source change token. Product and configuration schema versions must match the source board version. Mismatch emits `CCSB-COMPAT-PROJECTION-METADATA-MISMATCH` and blocks runtime use.

## Done Evidence

- Foundation schema manifest updated with explicit board-version and runtime-projection compatibility metadata fields.
- Foundation schema static validator now asserts the required compatibility fields and choice options.
- Data dictionary CSV and markdown documentation updated.
- T02 static validator and report prove the bindings against the source schema and T01 compatibility contract.
