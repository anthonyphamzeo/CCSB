# US-002-T03 - Pre-Activation Compatibility Validation

**Status:** Implemented executable validation contract and reference engine  
**Task:** Validate configuration, mappings, feature flags, migrated data, and runtime projection before activation  
**Contract:** `docs/design/api-contracts/compatibility/US-002-T03-preactivation-compatibility-validation.json`

## Runtime Boundary

The repository does not yet contain the board Custom API plug-in project. T03 therefore supplies the deterministic validation core and the Dataverse integration contract consumed by `ccsb_ValidateBoardVersion` and `ccsb_ActivateBoardVersion`. The Python reference engine is executable release evidence; production plug-in code must preserve its inputs, rule semantics, codes, ordering, and fail-closed outcome.

Validation evaluates every rule group without short-circuiting so one run returns the complete remediation set. A warning-only result may activate. Any `blocking` or `error` diagnostic returns `allowed: false`.

## Configuration and Evidence

The validator requires a Ready board version, product/schema metadata, a configuration hash, and three current checks: normalized configuration completeness, current hash, and current board validation. Missing evidence emits `CCSB-COMPAT-EVIDENCE-MISSING`; a failed check or ineligible lifecycle emits `CCSB-COMPAT-CONFIGURATION-INVALID`.

Each check is bound to the current configuration hash. Evidence for a different hash emits `CCSB-COMPAT-VALIDATION-STALE`.

## Version and Migration Validation

- Product and configuration schema versions must match the supported V1 contract.
- A persisted version newer than the target is an unsupported downgrade.
- Migration state must be `None` or `Completed`.
- Compatibility metadata, projection-version backfill, and protected-record integrity checks must pass.
- Failed, missing, or incomplete migration evidence blocks activation with record-level diagnostics.

## Mapping Validation

Enabled entity definitions must use `Native CCSB` or `Customer Owned` sources and carry current valid metadata. Required semantic field mappings must resolve, and source/target types or governed transformations must be compatible. Required relationships must resolve with valid endpoints, cardinality, and navigation metadata.

Diagnostics include the affected configuration record and field where available. The engine never accepts an unresolved required mapping merely because another mapping with the same display label exists.

## Feature Flags and Live Schema

The selected V1 path requires:

1. `ccsb.foundation.schema.1.0.0.1`
2. `ccsb.runtime.projection.1.0.0`

Flags are explicit inputs from governed environment configuration; absent means disabled. The live schema report must be present, current for solution `1.0.0.1`, and have zero blocking diagnostics.

## Runtime Projection Validation

Exactly one projection supplied as current must be `Valid`, match the board product/configuration versions, use projection schema `1.0.0`, and bind to the current configuration hash and source change token. Missing, failed, or hash-stale projection evidence emits `CCSB-COMPAT-PROJECTION-STALE`; version mismatch emits `CCSB-COMPAT-PROJECTION-METADATA-MISMATCH`.

## Stale Validation Protection

The validation token is scoped to board version ID, configuration hash, target versions, evidence fingerprint, and Dataverse row version. `ccsb_ActivateBoardVersion` re-reads these values. Any change invalidates the result and forces validation again.

## Activation Denial

Activation uses a structured denial rather than throwing after data writes:

- `customApiSucceeded: false`
- active board pointer unchanged
- board lifecycle unchanged
- validation diagnostics and failed operation evidence retained
- primary code `CCSB-COMPAT-ACTIVATION-BLOCKED`

The active pointer changes only inside the activation transaction after a current allowed result is confirmed.

## Persistence

Each diagnostic becomes one `ccsb_configurationvalidationresult` row. `ccsb_detailjson` carries rule ID, expected/actual values, target versions, evidence fingerprint, and this catalog’s remediation link. Board validation/compatibility status and the failed or successful `ccsb_operation` are updated with the same correlation and validation-run identifiers.

## Verification

```powershell
python tools/validation/compatibility/US-002-T03-reference-validator.py --self-test
python tools/validation/compatibility/US-002-T03-static-validator.py
```

The reference fixtures cover a fully compatible board and a deliberately incompatible board that exercises every validation group.
