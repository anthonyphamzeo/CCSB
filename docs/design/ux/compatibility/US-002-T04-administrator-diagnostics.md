# US-002-T04 - Administrator Compatibility Diagnostics

**Status:** Started design contract and static validation  
**Task:** Design administrator diagnostics  
**Contract:** `docs/design/ux/compatibility/US-002-T04-administrator-diagnostics.json`

## Scope

US-002-T04 defines the configuration-administration surface that lets a Configuration Administrator understand why a Board Version is compatible, compatible with warnings, or blocked. The design uses existing CCSB records created by US-002-T02 and US-002-T03:

- `ccsb_boardversion` for product/schema version, migration, validation, lifecycle, and configuration-hash state.
- `ccsb_configurationvalidationresult` for each blocking, error, warning, or informational diagnostic.
- `ccsb_runtimeprojection` for current projection status and projection error detail.
- `ccsb_operation` for validation command evidence, idempotency keys, correlation IDs, result JSON, and errors.

The UX does not require access to plug-in trace logs or server logs. Server-side logs remain support-only backup evidence, not the administrator's primary diagnosis path.

## Admin Workflow

1. The administrator opens a Board Version from configuration administration.
2. The Compatibility Diagnostics summary shows lifecycle, validation status, compatibility status, migration state, product version, configuration schema version, configuration hash, and last validation run time.
3. The Blocking Diagnostics grid shows open blocking/error validation results scoped to the selected Board Version.
4. The Remediation panel groups diagnostics by category and shows the exact affected record, field, message, and recommended action.
5. If migration or metadata backfill is required, the panel shows the approved action path and warns that activation remains blocked until validation passes again.
6. The administrator runs the safe Validate Compatibility command.
7. The command writes operation and validation-result evidence, refreshes the summary and grids, and never changes the active board pointer.

## Compatibility State Summary

The Board Version form gets a Compatibility Diagnostics section on the Lifecycle tab. It must show:

| Field | Purpose |
|---|---|
| `ccsb_compatibilitystatus` | Current compatibility outcome used by activation. |
| `ccsb_migrationstate` | Whether migration is not needed, pending, running, completed, failed, or blocked. |
| `ccsb_productversion` | CCSB product version that validated this Board Version. |
| `ccsb_configurationschemaversion` | Normalized configuration schema version. |
| `ccsb_validationstatus` | Latest validation status. |
| `ccsb_validationrunon` | Time of the last validation run. |
| `ccsb_configurationhash` | Current source hash used to detect stale validation. |
| `ccsb_lifecyclestate` | Whether the version is Draft, Validating, Ready, Active, Superseded, or Retired. |

The section must use text labels and status icons together so administrators do not have to infer status from color alone.

## Blocking Diagnostics Grid

The primary diagnostics grid is scoped to the current Board Version and defaults to open blocking/error results. It must show:

| Column | Reason |
|---|---|
| `ccsb_validationcode` | Stable support and remediation code. |
| `ccsb_severity` | Blocking, Error, Warning, or Information. |
| `ccsb_resultstatus` | Open, Accepted, Resolved, or Suppressed. |
| `ccsb_validationcategory` | Area that failed. |
| `ccsb_affectedentitylogicalname` | Failed component table. |
| `ccsb_affectedrecordid` | Failed component record. |
| `ccsb_affectedfieldlogicalname` | Failed field, if field-scoped. |
| `ccsb_message` | Human-readable issue summary. |
| `ccsb_recommendedaction` | Administrator remediation. |
| `ccsb_detectedon` | Detection time. |

The grid should sort by severity, then category, then detected time. Detail JSON remains available on the validation result form for specialist review, but the grid cannot require reading raw JSON to understand the next action.

## Migration And Remediation Actions

The Remediation panel maps every US-002-T03 compatibility code to an administrator action. The panel must separate:

| Action family | Examples | UX behavior |
|---|---|---|
| Configuration repair | missing mappings, type mismatches, invalid configuration | Link to the affected configuration record and field. |
| Metadata and migration repair | missing metadata, migration required, migrated data invalid | Link to the approved backfill or migration runbook, then prompt for safe re-validation. |
| Runtime projection repair | stale projection, projection metadata mismatch | Link to projection generation evidence and show current projection status/error detail. |
| Release gate repair | live schema blocked, feature flag disabled, evidence missing | Link to the operation or release gate evidence record. |
| Unsupported path repair | product/schema unsupported, downgrade blocked | Show forward-only upgrade guidance and keep activation disabled. |

Migration actions are guidance and controlled operation entry points only. T04 does not introduce an automatic migration command in the admin form. If migration automation is added later, it must write `ccsb_operation` evidence and must still require a separate compatibility validation pass before activation.

## Safe Re-validation Command

The command label is **Validate Compatibility** and it calls only `ccsb_ValidateBoardVersion`.

Required command behavior:

- Available from the Board Version diagnostics surface for Draft, Validating, Ready, or Active versions.
- Requires confirmation that the command does not activate the version.
- Requires an idempotency key derived from Board Version ID, configuration hash, target versions, requesting user, and request time bucket.
- Re-reads the Board Version row version, configuration hash, target versions, evidence fingerprint, and current projection before evaluating.
- Writes one `ccsb_operation` record with Operation Type `Validate Board Version`.
- Writes or updates `ccsb_configurationvalidationresult` rows with stable validation codes and recommended actions.
- Refreshes the summary, diagnostics grid, projection health, and operation evidence after completion.
- Does not call `ccsb_ActivateBoardVersion`.
- Does not mutate active board pointers, board lifecycle, publish state, or schedule records.

The command is safe to retry. Duplicate clicks with the same idempotency key must return the existing operation/result evidence rather than create competing validation runs.

## Evidence And Audit

The diagnostics workspace must expose the latest validation operation and its evidence:

- `ccsb_operationtype`
- `ccsb_operationstatus`
- `ccsb_correlationid`
- `ccsb_idempotencykey`
- `ccsb_requestedon`
- `ccsb_startedon`
- `ccsb_completedon`
- `ccsb_resultjson`
- `ccsb_errorsummary`
- `ccsb_errordetail`

Administrators should be able to copy the validation code, affected record ID, operation ID, and correlation ID for support without opening server logs.

## Security And UX Rules

- Configuration Administrators can read diagnostics and run safe validation.
- Support readers can read diagnostics and operation evidence but cannot run commands.
- Activation remains a separate command and is hidden or disabled while compatibility status is blocked.
- Suppress, accept, or resolve actions require a resolution note and must not hide blocking activation checks from the activation service.
- Detail JSON and error detail fields remain visible only to administrator/support roles because they may contain implementation details.

## Data And Schema Bindings

The design binds to existing schema fields and relationships only. No new tables are required for T04. Required relationships are:

- Board Version to Validation Results.
- Operation to Validation Results.
- Board Version to Runtime Projections.
- Board Version to Operations.

These relationships let administrators move from a blocked Board Version to the failing component and back to the operation that produced the evidence.

## Validation

```powershell
python tools/validation/compatibility/US-002-T04-static-validator.py
```

The static validator checks the UX contract, source diagnostic catalog coverage, schema bindings, relationships, safe command behavior, and acceptance gates.
