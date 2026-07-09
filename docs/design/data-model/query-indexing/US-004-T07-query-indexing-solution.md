# US-004-T07 Query and Indexing Solution

**Task:** Review query and indexing shapes  
**Decision:** Approved as the reference query plan. Recheck confirms the P0 table blocker is cleared in `tools/provisioning/CCSB.AuditEntities/schema/csb.auditentities.schema.json`; the remaining gate is Dataverse performance evidence.

## Verified Schema Evidence

`CSB_AuditEntities` now provisions `ccsb_publishlock`, `ccsb_schedulechange`, `ccsb_publishsnapshotitem`, and `ccsb_resourcecapability`. The manifest also contains `out/CSB_AuditEntities_1_0_0_0_unmanaged.zip`. Confirmed keys are `ccsb_lockkey`, `ccsb_changekey`, `ccsb_snapshotitemkey`, and `ccsb_capabilitykey`. Ownership is organization-owned for lock/change/snapshot item and user-owned for resource capability.

## Query Contract

CCSB runtime reads must use Custom APIs or server-owned QueryExpression/FetchXML contracts. The PCF must not compose arbitrary Dataverse queries. Every runtime query must include board scope, active configuration version or schedule version, an explicit column set, server paging, and a bounded date or key predicate. JSON payload columns such as projection, scope, manifest, before/after image, and detail fields are not filter columns.

## Reference Query Shapes

| Use case | Required filters | Notes |
|---|---|---|
| Board bootstrap | `ccsb_boardcode` or schedule board ID, active board, active `ccsb_boardversion`, current valid `ccsb_runtimeprojection` | Load configuration from projection first; normalized tables remain source of truth. |
| Projection load | `ccsb_boardversionid`, `ccsb_projectiontype`, `ccsb_scopetype`, `ccsb_scopekey`, `ccsb_iscurrent`, `ccsb_projectionstatus` | Return one current payload; reject stale, failed, expired, or schema-incompatible projections. |
| Source record lookup | board/schedule scope, `ccsb_sourceentitylogicalname`, `ccsb_sourcerecordid` | Applies to native mirrors, schedule changes, operation items, and snapshot items. |
| Visible schedule slice | board or schedule version, `plannedStart < rangeEnd`, `plannedEnd > rangeStart`, optional group/resource/location/status | Use overlap predicates, not client-side filtering. Page deterministically by start time then ID. |
| Resource eligibility | `ccsb_resourceid`, `ccsb_resourceroleid`, `ccsb_capabilitytype`, `ccsb_capabilitycode`, effective range, `ccsb_iseligible`, `ccsb_capabilitystatus` | Use `ccsb_resourcecapability`; no JSON eligibility scans. |
| Lock check | `ccsb_boardid`, `ccsb_lockstatus`, `ccsb_scopetype`, `ccsb_scopefromutc`, `ccsb_scopetoutc`, optional group/resource/item | Use `ccsb_publishlock` and durable `ccsb_lockkey`. |
| Publish evidence | `ccsb_publishsnapshotid`, `ccsb_sequence`, `ccsb_capturestatus`, source record fields, schedule item/assignment/resource lookups | Use `ccsb_publishsnapshotitem` below header JSON. |
| Pending/applied changes | `ccsb_boardid`, `ccsb_scheduleversionid`, `ccsb_changestatus`, target/source record, `ccsb_requestedon`, `ccsb_committedon`, `ccsb_publishedon` | Use `ccsb_schedulechange` for preview, audit, publish, and rollback queries. |

## Index and Key Expectations

Use Dataverse-supported primary IDs, lookup indexes, state/status columns, and alternate keys; do not assume arbitrary SQL indexes. Required alternate keys are: board code, board-version number per board, runtime projection scope, operation correlation ID, operation item key per operation, source record identity per board, publish lock key, schedule change key, and publish snapshot item key. Lookup-heavy filters must keep direct lookups for board, board version, schedule version, resource, schedule item, assignment, operation, snapshot, and lock.

## Acceptance Gates

Performance seeding must cover a 31-day visible range, 100 resources, 5,000 working schedule records, mapped source lookups, active locks, publish snapshots, schedule changes, capabilities, and stale projections. A query is accepted only if it is bounded, uses indexed/key predicates, returns a minimal column set, avoids deep joins, and has captured p50/p95 timing evidence. T07 can move from schema-blocked to performance-validation pending.
