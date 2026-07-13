# US-070-T01 - Permission Model and Matrix

## Purpose

US-070-T01 defines the V1 CCSB permission model for Custom APIs, plug-ins, PCFs, model-driven administration, support diagnostics, and release tests.

The controlling rule is simple: CCSB permissions never grant access that Dataverse does not already allow. Dataverse table, row, business-unit/team, sharing, and field-security checks are evaluated first. CCSB permission profiles and assignments only further restrict the effective action set.

## Security Principles

- Dataverse is the outer authorization boundary for customer data.
- CCSB action permissions are restrictive product permissions, not grants.
- All schedule mutation, publish, rollback, configuration activation, diagnostics, and integration actions are server-authoritative.
- PCF controls may request actions but cannot assert identity, role, scope, privilege, board, profile, or assignment.
- Missing profile, missing assignment, disabled assignment, expired assignment, stale board version, unknown action, or unknown scope fails closed.
- Denials use stable diagnostic codes and do not disclose protected record content, field values, or inaccessible record existence.

## Evaluation Order

Every protected action uses this order:

1. Resolve the platform caller from the Dataverse execution context.
2. Verify required Dataverse privileges for all referenced CCSB and customer-owned tables.
3. Apply Dataverse row ownership, team membership, sharing, and business-unit access.
4. Apply Dataverse field-security checks for mapped fields, payload JSON, reason fields, diagnostics, and error details.
5. Resolve enabled `ccsb_permissionassignment` rows for the caller, team, or application principal.
6. Resolve enabled `ccsb_permissionprofile` action flags for the active board version.
7. Intersect requested board, version, group, location, resource, time, and field-policy scope with assignment scope.
8. Apply command policy such as lifecycle state, lock state, confirmation token, row version, idempotency key, and rollback compatibility.
9. Return an allow/deny decision with correlation and support-safe diagnostics.

If any step cannot be evaluated, the result is deny.

## Personas

| Persona | Purpose | Default profile intent |
|---|---|---|
| Admin | Maintains configuration, permission profiles, assignments, compatibility diagnostics, and integration settings. | Configuration and audit access; no schedule mutation by default. |
| Scheduler | Performs operational schedule reads, draft changes, assignment, validation, and governed conflict override. | Schedule operation access; no publish or rollback. |
| Publisher | Previews, publishes, rolls back, and reviews publish/audit evidence. | Publish/rollback and publish evidence access; no draft edit. |
| Support | Troubleshoots with redacted diagnostics and audit evidence. | Diagnostics only; no raw customer schedule content or mutation. |
| Unauthorised | Has no effective CCSB profile assignment. | Every protected action denied. |

## CCSB Action Catalog

The machine-readable matrix is `tests/Fixtures/Security/US-070-T01-permission-matrix.json`.

| Action | Profile flag | Admin | Scheduler | Publisher | Support | Unauthorised | Dataverse prerequisite summary |
|---|---|---:|---:|---:|---:|---:|---|
| View schedule | `ccsb_canviewschedule` | No | Yes | Yes | No | No | Read permitted board/projection records and mapped source rows. |
| Create schedule | `ccsb_cancreateschedule` | No | Yes | No | No | No | Create schedule-change evidence and create/write permitted target rows through API. |
| Edit schedule | `ccsb_caneditschedule` | No | Yes | No | No | No | Read/write permitted target rows and CCSB change/audit rows. |
| Assign resources | `ccsb_canassignresources` | No | Yes | No | No | No | Read eligible resources/requirements and write governed assignments. |
| Override conflicts | `ccsb_canoverrideconflicts` | No | Yes | No | No | No | Read conflict evidence, write reason, and satisfy command policy. |
| Manage configuration | `ccsb_canmanageconfiguration` | Yes | No | No | No | No | Read/write configuration and permission tables through server commands. |
| Validate board version | `ccsb_canmanageconfiguration` | Yes | No | No | No | No | Read configuration and create validation result evidence without activating pointers. |
| Publish schedule | `ccsb_canpublish` | No | No | Yes | No | No | Read publish scope, create snapshot/lock/audit rows, and write permitted official-state fields. |
| Rollback schedule | `ccsb_canrollback` | No | No | Yes | No | No | Read compatible snapshot and restore only rollback-managed fields through API. |
| View audit | `ccsb_canviewaudit` | Yes | No | Yes | Yes | No | Read audit rows and only linked rows already visible through Dataverse. |
| Support diagnostics | `ccsb_canviewaudit` | Yes | No | Yes | Yes | No | Read redacted operation/audit evidence only. |
| Manage integrations | `ccsb_canmanageintegrations` | Yes | No | No | No | No | Read/write integration policy without exposing secrets. |

## Scope Dimensions

| Dimension | Source | Required behavior |
|---|---|---|
| Board | `ccsb_permissionassignment.ccsb_boardid` or resolved board registry | Required for board-bound actions. |
| Board version | `ccsb_permissionprofile.ccsb_boardversionid` and requested command version | Binds profile flags to the active or requested configuration version. |
| Location | Assignment location scope or resolved schedule/resource location | Restricts operational locations when configured. |
| Group | Assignment group/team scope or configuration group | Restricts scheduling and publish scope to configured groups. |
| Resource | Resolved resource or candidate resource from command payload | Required for assignment and eligibility decisions. |
| Time window | Command date range, publish scope, or lock scope | Required for visible slice, lock, publish, and rollback decisions. |
| Field policy | `ccsb_fieldmapping` plus Dataverse field security | Required before values are returned, changed, published, restored, or logged. |

An assignment with narrower scope wins over a broader profile. Multiple assignments are unioned only after Dataverse permits each referenced row; deny/restrict assignments can remove access from the candidate set.

## Dataverse Security Relationship

CCSB authorization must use supported Dataverse APIs or services that evaluate the caller's effective privileges. The CCSB service must not trust client-provided table names, record IDs, field names, role names, principal IDs, profile IDs, board IDs, or scope IDs. Payload references are identifiers to re-resolve, not authorization evidence.

For mapped customer-owned tables, CCSB verifies both the mapped table/field policy and the caller's Dataverse access to the actual source or target row. If a user can edit a CCSB profile but cannot read a customer booking row, the profile still cannot be used to reveal that booking.

Field-secured values are inaccessible unless the caller has the relevant field-security profile. Denials may name the action and diagnostic code, but not the protected field value or inaccessible record title.

## Required Negative Cases

| Category | Required result |
|---|---|
| No Dataverse privilege | Deny before profile evaluation; do not reveal CCSB scope details. |
| Field security denied | Deny or redact protected fields; do not echo values in logs or diagnostics. |
| Missing CCSB profile | Deny with `CCSB-SEC-PROFILE-MISSING`. |
| Disabled or expired assignment | Deny with `CCSB-SEC-ASSIGNMENT-INACTIVE`. |
| Out-of-scope board | Deny with `CCSB-SEC-SCOPE-DENIED`. |
| Forged payload scope | Re-resolve server side and deny with `CCSB-SEC-FORGED-SCOPE`. |
| Publish or rollback without profile flag | Deny with `CCSB-SEC-ACTION-DENIED`. |
| Support raw payload request | Return redacted diagnostics and `CCSB-SEC-FIELD-REDACTED`. |
| Direct client mutation | Deny because mutations must use Custom APIs. |

## Server Contract for US-070-T03

The authorization service should expose a single decision contract containing `action`, server-resolved `caller`, `requestedScope`, `resolvedScope`, `allowed`, `diagnostics`, support-safe `effectivePermissions`, and `correlationId`.

The service must be invoked for every Custom API and any diagnostic/configuration read that could disclose protected configuration or schedule data.

## Testing Contract for US-070-T05

Automated role tests should load the JSON matrix and execute:

- One positive case for every persona/action marked allowed.
- One negative Dataverse privilege case for each mutating action family.
- Scope-denial cases for board, group/location, resource, time window, and field policy.
- One forged-payload case per Custom API family.
- One unauthorised persona case for every protected action.
- One support redaction case proving diagnostics do not leak raw payload or protected fields.

Passing these tests proves that CCSB permission cannot bypass Dataverse security.

## Verification

The static validator `tools/validation/security/US-070-T01-static-validator.py` checks required personas, profile flags, action prerequisites, Dataverse-first policy, negative cases, diagnostics, and acceptance gates. It writes `docs/implementation/testing/evidence/US-070-T01/static-report.md`.

This is design and static contract evidence only. Runtime enforcement remains US-070-T03, permission-aware UI behavior remains US-070-T04, connected positive/negative role tests remain US-070-T05, and managed-solution role packaging remains US-070-T06.
