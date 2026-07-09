# CCSB V1 — Complete Task-Level Design and Delivery Plan

**Source basis:** CCSB Consolidated Project Document v2.1 — PCF Controls Added (4 July 2026), CCSB Task-Level Design and Delivery Plan v1.0, and CCSB Deep Market Research, Competitive Analysis & Long-Term Viability (21 June 2026).

**Scope rule:** This design retains the V1 boundary: native Dataverse Online, desktop Model-driven App, custom Fluent UI React PCF, server-authoritative Custom APIs, normalized `ccsb_*` configuration, and no V1 split/merge, external connectors, mobile/offline, URS adapters, virtual/external sources, multi-path grouping, or autonomous AI writes.

## Decision: missing database/data-model story

**Result: missing.** The controlled baseline contains a logical data model and data-mapping stories, but it explicitly requires the solution build to confirm the physical Dataverse schema. The existing backlog has no dedicated story for product-owned `ccsb_*` table implementation, keys, relationships, ownership, lifecycle values, retention and migration. **US-004** is therefore added as a P0 V1 foundation story. It is a blocking dependency for configuration, permissions, audit, publish/rollback and ALM.

## Backlog statistics

- **10 epics**: E01–E10; **40 stories** including US-004 and the two PCF-control stories, US-014 and US-029.
- **36 V1 stories** and **4 Later stories** retained as design gates.
- **249 implementation tasks** with task category, definition of done, dependency, risk and traceability.

## Recommended delivery plan

| Phase | Stories | Outcome | Exit gate |
|---|---|---|---|
| Phase 0 — Product & architectural foundation | US-001, US-004, US-002, US-070, US-071, US-003 | Managed solution scaffold; physical schema; compatibility contract; security model; versioned Custom API envelope; board/environment isolation. | Clean installation succeeds; physical schema and security matrix are approved; API and schema compatibility checks fail closed. |
| Phase 1 — Safe configuration platform | US-010–US-014, US-020–US-022 | Immutable version lifecycle; mapped/native graph; write/rollback policy; projection; groups; roles; requirements/capacity; guided Configuration Studio PCF. | A mapped graph and optional native graph validate, activate, generate a projection, resolve a single group path and can be safely authored through the Configuration Studio. |
| Phase 2 — Runtime PCF foundation and read-only operational workspace | US-029–US-033 | Projection-controlled Runtime PCF, board context, virtualised timeline, server paging, filters/preferences, overlays and timezone-correct read model. | Runtime starts only with a valid projection; reference board slice loads within target budgets, no stale response replaces current context, and overlays degrade safely. |
| Phase 3 — Controlled schedule operations | US-040–US-044, US-050–US-051 | Create/edit; assign/unassign; move/resize/reassign; status; overrides; requirement calculation; rule/confirmation pipeline. | All operations use validate → optional confirmation → execute → audit → targeted refresh with concurrency/idempotency. |
| Phase 4 — Workbenches and release governance | US-052–US-053, US-060–US-063, US-072 | Conflict and unscheduled workbenches; publish preview; immutable snapshots; locks; field-scoped rollback; support correlation. | Publish and rollback are atomic, evidence-backed, scoped and recoverable; support trace works end to end. |
| Phase 5 — Production-release evidence | US-080–US-082 | Reference performance suite; accessibility verification; upgrade rehearsal; support runbook; release gates. | Measured performance, accessibility, install/upgrade, rollback and support evidence meet release approval criteria. |

### Critical path
1. `US-001 → US-004 → US-002 → US-010 → US-011 → US-012 → US-013 → US-014`
1. `US-004 → US-070 → US-071`
1. `US-001 + US-003 + US-013 + US-070 + US-071 → US-029 → US-030 → US-031`
1. `US-011 + US-012 + US-070 + US-071 → US-040 → US-041 → US-042`
1. `US-022 + US-070 + US-071 → US-051 → US-060 → US-061 → US-062`
1. `US-071 → US-072; then US-080 + US-081 → US-082`

### Parallel work
- **After US-004:** US-002, US-070, and the physical-schema test data factory can proceed in parallel.
- **After US-010/US-011:** US-012, US-020, and US-022 can proceed in parallel; US-013 follows once mappings/policies are stable. US-014-T01/T02 can use fixed fixtures in parallel, but the Configuration Studio must not integrate activation or projection workflows until the backend contracts are complete.
- **After US-013 plus US-070/US-071:** US-029 establishes the Runtime PCF boundary, projection bootstrap and shared command/read contracts. US-030–US-033 then build their operational capabilities against that foundation.
- **After US-030:** US-031 runtime virtualisation and US-032 command-bar/filter UX can run in parallel; US-033 starts once the read-model mapping contract is stable.
- **After US-071:** US-040/US-044 command surfaces can proceed alongside rule pipeline work in US-051; US-041 depends on the first operation contract.
- **After core operations:** US-050/US-053, US-052/US-072, and US-060 publish preview can progress in parallel, provided shared audit/rule DTOs are versioned.
- **Throughout:** US-080 performance instrumentation and US-081 accessibility architecture begin in Phase 0 and mature through every increment; do not leave them until release week.

### Architectural prerequisites
- A single source-controlled solution/repository structure with automated managed-solution import, clean-environment test, dependency/SBOM checks and a release evidence store.
- The physical `ccsb_*` schema (US-004), including alternate keys, relationships, ownership, lifecycle states, audit/snapshot controls and a deterministic test-data factory.
- An immutable board-version and generated runtime-projection contract, including product/schema/projection compatibility validation.
- One scheduler time contract: UTC persistence, board IANA timezone, Luxon only for scheduling-domain calculations, and explicit DST test cases.
- A typed mapping/query/command boundary: the PCF reads only visible slices; all mutations use versioned Custom APIs with authorization, validation, idempotency and row-version concurrency.
- A rule/permission/audit contract shared by validation, execution, publish/rollback and support diagnostics.
- Reference performance and accessibility test harnesses before the custom timeline becomes feature-rich.

## PCF Controls — Sequential Implementation Guide

The two new PCF stories are **experience and orchestration layers**. They do not replace the backend stories that own schema, metadata validation, board-version lifecycle, projection generation, security or Custom API enforcement.

### Implementation rules

1. **Complete the server contract before relying on the PCF.** A PCF task may use fixtures or mocked DTOs during early construction, but it must not become the source of truth or introduce an alternative write path.
2. **Use one work item branch per task.** A task is ready only when its predecessor story/task evidence, API contract and data fixture are available. Do not mix schema changes, PCF UX, and uncontrolled customer mapping changes in the same pull request.
3. **Validate on every draft save.** Client validation improves usability; server-side validation remains authoritative. The user interface must always preserve the server result, correlation ID and field-level diagnostics.
4. **No direct write boundary.** Configuration Studio writes only through lifecycle/configuration services and Custom APIs. Runtime PCF reads visible slices through approved read contracts and writes only through versioned Custom APIs.
5. **Complete testing before hand-off.** Each task must demonstrate its Definition of Done, unit/component evidence, integration evidence where applicable, accessibility evidence for custom UI, and updated operational documentation.

### US-014 — Configuration Studio task sequence

| Sequence | Task(s) | Entry gate | Exit / hand-off |
|---|---|---|---|
| 1 | US-014-T01 | US-010 to US-013 design contracts are available. | Approved PCF boundary, information architecture and workflow specification. |
| 2 | US-014-T02 | Solution scaffold and security baseline exist. | Deployable PCF host shell with no direct-write implementation. |
| 3 | US-014-T03 | Board-version lifecycle APIs are stable. | Draft/session facade with clone, compare and concurrency behavior. |
| 4 | US-014-T04, US-014-T05, US-014-T06 | Metadata, grouping/role and permission services are available. | Mapping, grouping/capacity, status/rule/permission modules can progress in parallel after the shared draft facade is complete. |
| 5 | US-014-T07 | All configuration editors save valid draft records. | Compare, validate, projection and activation workbench; no activation with blockers. |
| 6 | US-014-T08 | Command paths are wired. | Security, audit, field-security and concurrency controls are verified. |
| 7 | US-014-T09, US-014-T10 | Integrated studio is feature complete. | Functional/accessibility and representative-metadata performance evidence. |
| 8 | US-014-T11 | Tests and performance evidence pass. | Managed-solution deployment, support fallback and administrator guidance. |

### US-029 — Runtime PCF and Projection Controller task sequence

| Sequence | Task(s) | Entry gate | Exit / hand-off |
|---|---|---|---|
| 1 | US-029-T01 | Projection, security and API contracts are approved. | Runtime boundary and DTO/state contract are frozen. |
| 2 | US-029-T02 | Solution scaffold and permitted-board service exist. | Deployable PCF host shell with accessible failure states. |
| 3 | US-029-T03 | Active board/version and runtime projection are available. | Fail-closed projection controller prevents invalid runtime start. |
| 4 | US-029-T04 | Projection mapping contract is stable. | Visible-slice reads, cache keys and cancellation behavior are available to the timeline/read stories. |
| 5 | US-029-T05 | Bootstrap and read client exist. | Shared runtime state enables US-030 to US-033 without duplicated board context logic. |
| 6 | US-029-T06, US-029-T07 | Versioned Custom API envelopes are stable. | Reusable command adapter and targeted-refresh controller for US-040 to US-063. |
| 7 | US-029-T08 | Runtime reads/commands are connected. | Secure telemetry, correlation and support-safe diagnostics. |
| 8 | US-029-T09 | Runtime foundation is integrated. | Contract, security, performance and accessibility evidence. |
| 9 | US-029-T10 | Runtime tests pass and packaging prerequisites are ready. | Managed deployment and support guidance. |

### Story-level delivery order

```text
US-001 → US-004 → US-002
                 ├→ US-010 → US-011 → US-012 → US-013 → US-014
                 ├→ US-020 → US-021
                 └→ US-022

US-004 → US-070 → US-071
US-001 + US-003 + US-013 + US-070 + US-071 → US-029 → US-030 → US-031 → US-032 / US-033
US-029 + US-071 → US-040 / US-041 / US-042 → US-050 / US-051 → US-060 → US-061 → US-062
```

**Parallelism rule:** US-014-T02 can start with fixed fixture data once the PCF boundary is approved, but T03–T08 must integrate only with the final backend contracts. US-029-T02 can start after US-001/US-003, while T03 onward must use the active projection/API contracts. Performance and accessibility tests begin as soon as either PCF shell renders; they are not deferred to the release phase.


### Principal delivery risks and controls
| Risk | Control |
|---|---|
| Scope and competitive overlap | Keep V1 inside the governed Dataverse custom-operations wedge; explicitly disqualify payroll, mobile workforce, routing/optimisation and universal URS replacement opportunities. |
| Implementation variability | Enforce supported mapping patterns, validated configuration templates, resolver contracts and a two-customer evidence rule before accepting new product capability. |
| Data/rule correctness | Use mapping preflight, deterministic rule results, test board fixtures, confirmation/validation, immutable audit and publish/rollback evidence. |
| Performance | Use visible-slice queries, server paging, virtualisation, query budgets, telemetry and a reference data profile; no environment-wide preload. |
| Enterprise trust | Gate release on managed install/upgrade rehearsal, least-privilege security, support runbook, performance proof and accessibility evidence. |

### Commercial-readiness workstream (parallel; not a V1 feature expansion)
| ID | Activity | Definition of done |
|---|---|---|
| MR-01 | Define one beachhead ICP and anti-ICP | Publish a qualification scorecard that screens out payroll, consumer booking, routing-heavy field service and broad WFM use cases. |
| MR-02 | Create design-partner success scorecard | Measure scheduling cycle time, conflict rate, unfilled requirement rate, publish recovery incidents and custom code avoided. |
| MR-03 | Create two validated configuration templates | Productise only mapping/rule patterns repeated across at least two design partners; include seed data and implementation guide. |
| MR-04 | Prepare buyer/security/support evidence pack | Package architecture, data-handling, roles, performance, upgrade, limitations and support responsibility material before commercial pilots. |

## Detailed backlog: Epic → User Story → Tasks

## E01 - Product foundation and ALM

### US-001 — As a solution administrator, I want to install CCSB as a managed solution with required roles and environment settings so that the product is governed through standard ALM.

**Priority / release:** P0 / V1  
**Phase:** Phase 0 — ALM & solution scaffold  
**Dependencies:** None  
**Primary risk:** Managed-solution dependency/import drift  
**Traceability:** FR-ALM-001; NFR-ALM-001  
**Acceptance outcome:** Import validates required components; roles are installed; version is visible; unsupported dependencies fail clearly.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-001-T01 | Deployment | Create managed-solution baseline: Create solution structure for PCF, Dataverse tables, Custom APIs, plug-ins, security roles, forms/views, environment variables, and configuration schema assets. | Managed solution imports into a clean development environment with no unmanaged product components required. | L |
| US-001-T02 | Technical | Define component dependency manifest: Pin PCF, Fluent UI, dnd-kit, TanStack Virtual, Luxon, plug-in and build-tool versions; create SBOM and licence register. | Dependency manifest and SBOM are checked into source control; all licences are approved. | M |
| US-001-T03 | Data | Provision environment configuration: Define non-secret environment variables, connection-reference policy, default values and validation rules; prohibit board-record secrets. | Import prompts or validates every required environment setting and no secret is stored in ccsb_* configuration. | M |
| US-001-T04 | UX | Provide install verification surface: Add an administrator-facing version/build-status page or model-driven view showing solution version, schema version, installed roles and configuration validation shortcut. | Admin can confirm installation state without inspecting solution internals. | S |
| US-001-T05 | Validation | Implement preflight import checks: Validate prerequisite solution components, Dataverse version assumptions, role availability and schema version; emit actionable diagnostic codes. | Unsupported import/configuration fails closed with actionable remediation guidance. | M |
| US-001-T06 | Testing | Automate clean-environment install tests: Run import, post-import validation, role assignment, upgrade and uninstall-impact tests in an isolated Dataverse test environment. | Pipeline stores test evidence for clean install and failed-prerequisite scenarios. | L |
| US-001-T07 | Documentation | Publish installation and rollback runbook: Document prerequisites, import order, environment variables, role assignment, smoke tests, downgrade limitations and support hand-off. | Runbook is reviewed by release owner and used successfully in a rehearsal. | M |

### US-004 — **NEW DATA-MODEL STORY** · As a solution architect, I want CCSB's physical Dataverse data model, keys, relationships, ownership, lifecycle and retention controls implemented so that the product has a supportable, upgrade-safe data foundation.

**Priority / release:** P0 / V1  
**Phase:** Phase 0 — Data foundation  
**Dependencies:** US-001  
**Primary risk:** Incorrect physical model or destructive schema evolution  
**Traceability:** DM §6; FR-GPH-001; FR-CFG-002/003; FR-ALM-001; NFR-MNT-001; NFR-ALM-002  
**Acceptance outcome:** The managed solution contains documented ccsb_* tables, relationships, keys, choice/status lifecycles, security/ownership design, migration/seed strategy and validation for the optional native schedule graph.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-004-T01 | Data | Produce physical schema specification: Translate the logical model into a versioned Dataverse physical schema: tables, columns, data types, choices, lookups, ownership, requiredness, max lengths and labels. | Data dictionary is approved and traceable to the logical model; no ambiguous logical attribute remains. | L |
| US-004-T02 | Data | Implement product-owned configuration tables: Create ccsb_board, boardversion, entity/field/relationship mappings, group definitions, status models/transitions, roles, rules, permissions, projection and validation-result tables. | Tables, relationships and baseline forms/views are solution-aware and match the data dictionary. | L |
| US-004-T03 | Data | Implement control, audit and publish tables: Create operation, operation item, schedule change, conflict case, publish snapshot/header items, publish lock, audit log and reserved outbox tables with append-only/immutable policy. | Audit/publish entities support required relationships and prevent unsupported destructive edits through security and server controls. | L |
| US-004-T04 | Data | Implement optional native schedule graph: Create optional ccsb_scheduleitem, scheduleactivity, scheduleassignment, activity requirement, resource and resource capability tables or equivalent documented native schema. | A native-only board version can pass mapping validation and exercise the same operation contracts. | L |
| US-004-T05 | Data | Define keys, relationships and lifecycle values: Configure alternate keys, relationship cascade behaviour, uniqueness constraints, lifecycle/status reason choices, deletion policy, lookup targets and retention flags. | Key conflicts and unsupported cascade paths are rejected by automated schema tests. | M |
| US-004-T06 | Security | Define ownership and access model: Choose ownership types and privileges for product tables; align with environment governance, least privilege, data retention and support access. | Security matrix demonstrates admin, scheduler, publish manager, support analyst and unauthorised user behaviour. | M |
| US-004-T07 | Performance | Review query and indexing shapes: Document filters for board, active version, source record, resource, date range, lock and publish queries; validate that projections use bounded and supported Dataverse queries. | Reference query plan is approved and performance suite can seed/reference indexed access paths. | M |
| US-004-T08 | Validation | Create schema validation and compatibility checks: Implement metadata validation for required fields, types, relationship cardinality and schema versions for both mapped and native graph modes. | Incompatible schema is reported with record/field-level diagnostics before activation. | L |
| US-004-T09 | Testing | Build data factory and integrity test suite: Create deterministic seed data and tests for keys, relationships, status lifecycles, retention rules, native/mapped graph variants and migration defaults. | Schema tests run in CI and provide reproducible reference data for runtime/performance tests. | L |
| US-004-T10 | Deployment | Deliver schema migration and upgrade policy: Define additive migration rules, destructive-change prohibition, data backfill, feature flags, compatibility periods and rollback limits for managed solutions. | Upgrade rehearsal proves schema evolution without corrupting active boards or snapshots. | L |

### US-002 — As a release manager, I want configuration schema and product compatibility checks so that incompatible configurations do not activate after an upgrade.

**Priority / release:** P0 / V1  
**Phase:** Phase 0 — Compatibility contract  
**Dependencies:** US-004  
**Primary risk:** Configuration becomes incompatible after upgrade  
**Traceability:** FR-CFG-007; NFR-ALM-002  
**Acceptance outcome:** Validation detects incompatible schema; activation is blocked; diagnostics identify migration action.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-002-T01 | Technical | Define product and schema compatibility contract: Set semantic product version, configuration schema version, runtime projection version and minimum supported upgrade paths. | Compatibility contract is versioned and consumed by validation/activation. | M |
| US-002-T02 | Data | Add compatibility metadata: Persist product/schema/projection versions and migration state on board versions and runtime projections. | Every active board version reports unambiguous compatibility metadata. | M |
| US-002-T03 | Validation | Implement pre-activation compatibility validation: Validate current configuration, mappings, required feature flags and migrated data against target product version. | Activation fails with machine-readable codes and remediation links for each incompatibility. | L |
| US-002-T04 | UX | Design administrator diagnostics: Surface compatibility state, blocking records, migration action and a safe re-validation command in configuration administration. | Administrator can identify failed component and required remediation without server log access. | M |
| US-002-T05 | Testing | Test upgrade and downgrade boundaries: Cover compatible upgrade, required migration, invalid schema, stale projection, partial import and unsupported downgrade scenarios. | Automated tests verify fail-closed behavior and no active board is silently altered. | L |
| US-002-T06 | Deployment | Package migration scripts and release notes: Ship solution upgrade steps, configuration migration tooling, compatibility matrix and customer-facing release notes. | Upgrade package passes rehearsal from previous supported version. | M |

### US-003 — As a product owner, I want an environment-level board registry so that each Dataverse environment is an isolated CCSB tenant.

**Priority / release:** P1 / V1  
**Phase:** Phase 0 — Tenant/board boundary  
**Dependencies:** US-004, US-070  
**Primary risk:** Board/tenant isolation or permission leakage  
**Traceability:** Scope; DM  
**Acceptance outcome:** Board keys unique per environment; no cross-environment lookup/administration path exists.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-003-T01 | Data | Model board registry and tenant isolation: Define ccsb_board keys, active-version reference, environment boundary fields and uniqueness rules; prohibit cross-environment references. | BoardKey uniqueness is enforced per Dataverse environment and no cross-environment lookup is exposed. | M |
| US-003-T02 | Technical | Implement board resolution service: Resolve boards from current user, board permissions and active compatibility state; return only permitted board metadata. | Service returns no board outside current environment or user permissions. | M |
| US-003-T03 | UX | Build board selection and empty-state flow: Provide accessible selector, default board behavior, no-board state, invalid-board state and context change confirmation. | Users can select only authorised boards and understand unavailable/invalid states. | M |
| US-003-T04 | Validation | Enforce single active board version: Validate registry rules when activating/retiring versions and prevent orphaned active references. | Board cannot have zero/multiple active versions outside defined transition window. | M |
| US-003-T05 | Testing | Run isolation and authorisation tests: Test multiple boards, multiple users, invalid/retired boards and deliberately forged board IDs. | Negative tests prove no data or configuration leakage between boards/users. | M |
| US-003-T06 | Deployment | Seed sample registry records: Provide optional non-production sample board definitions and cleanup guidance. | Sample data is clearly non-production and removable without product schema impact. | S |

## E02 - Board configuration and runtime projection

### US-010 — As a board administrator, I want to create and clone board versions so that configuration changes do not alter an active board unexpectedly.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Configuration foundation  
**Dependencies:** US-004, US-002  
**Primary risk:** Active configuration is mutated or lifecycle bypassed  
**Traceability:** FR-CFG-001; FR-CFG-008  
**Acceptance outcome:** Active version cannot be edited; clone begins as Draft; compare shows changes.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-010-T01 | Data | Implement board-version aggregate: Create lifecycle fields and relationships for Draft, Validated, Active, Retired versions and clone lineage. | Only one active version is permitted and active records are immutable. | L |
| US-010-T02 | Functional | Implement create, clone, edit and compare flows: Support create, clone from version, edit draft, diff normalized configuration records and retain configuration lineage. | Clone produces an independent Draft; compare identifies additions, removals and changed values. | L |
| US-010-T03 | UX | Design version-management administration: Create model-driven views/forms for version status, validation state, source version, change summary, activation eligibility and retirement. | Administrator can complete lifecycle without editing raw JSON. | M |
| US-010-T04 | Validation | Protect immutability and lifecycle transitions: Enforce server-side transition policy and block direct edit/delete of active/retired artefacts outside approved retention administration. | Illegal lifecycle transitions are rejected and audited. | M |
| US-010-T05 | Testing | Test clone, compare and concurrent-edit cases: Cover clone fidelity, draft-only updates, activation race conditions, compare accuracy and soft-retirement behavior. | Automated tests confirm active version content is never changed by draft operations. | L |
| US-010-T06 | Deployment | Add version lifecycle migration and documentation: Ship data migration defaults, lifecycle runbook and configuration-change governance guide. | Release manager can promote a configuration change through documented lifecycle. | M |

### US-011 — As a board administrator, I want to map Booking, Activity, Assignment and Resource entities so that CCSB can use customer-owned Dataverse data.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Configuration foundation  
**Dependencies:** US-004, US-010  
**Primary risk:** Unsupported customer schema creates bespoke implementation  
**Traceability:** FR-CFG-003; FR-GPH-001  
**Acceptance outcome:** Metadata selectors validate tables/relationships; missing mandatory mapping blocks activation.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-011-T01 | Data | Define mapping semantic catalogue: Define required/optional semantic keys for Booking, Activity, Assignment and Resource roles, including IDs, relationships, planned times, names, status and capacity fields. | Catalogue is approved and used by UI, validation and runtime contracts. | L |
| US-011-T02 | Technical | Build Dataverse metadata discovery service: Read permissible table, field, relationship, choice and ownership metadata using supported APIs; enforce native Dataverse V1 source boundary. | Metadata service returns typed selectable candidates and never exposes unsupported sources. | L |
| US-011-T03 | UX | Build mapping administration wizard: Provide role-by-role table/field/relationship selection, compatibility hints, required-field indicators, relationship path preview and unsaved-change warnings. | Administrator can configure supported mapped graph without raw logical-name entry. | L |
| US-011-T04 | Validation | Validate graph cardinality and field types: Verify Booking→Activity→Assignment→Resource paths, required fields, date types, lookup targets and readable/writable privileges. | Invalid mappings are reported at field/path level and block validation/activation. | L |
| US-011-T05 | Technical | Create typed runtime mapping resolver: Generate a typed mapping/read-model object from normalized records for query construction and command parsing. | Runtime never hard-codes customer entity/field names and rejects mapping not present in active projection. | L |
| US-011-T06 | Testing | Test mapped and native graph modes: Exercise valid customer-mapped graph, missing relationship, bad choice type, invalid table permissions and optional native graph. | Contract tests demonstrate fail-closed mapping behavior. | L |
| US-011-T07 | Documentation | Publish supported mapping patterns: Document supported entity shapes, field requirements, relationship limitations and anti-patterns. | Implementation team can qualify mapping feasibility before build commitment. | M |

### US-012 — As a board administrator, I want to map write and rollback-managed fields separately so that CCSB changes only approved scheduling data.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Configuration foundation  
**Dependencies:** US-011  
**Primary risk:** Rollback overwrites non-managed customer data  
**Traceability:** FR-CFG-003; FR-RBK-002  
**Acceptance outcome:** Write and rollback flags independently stored; rollback cannot affect unmapped/unmanaged fields.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-012-T01 | Data | Add write and rollback flags to field mappings: Persist independently controlled read, write, rollback-managed and sensitive/display-only flags for every mapped semantic field. | No field defaults to writable or rollback-managed. | M |
| US-012-T02 | Functional | Create managed-field policy editor: Allow administrator to configure approved write/rollback fields with rationale and policy warnings. | UI makes write versus rollback scope explicit and cannot select unmapped fields. | M |
| US-012-T03 | Validation | Validate field policy safety: Reject rollback-managed fields not writable or not compatible with snapshot serialization; reject prohibited system/identity fields. | Validation produces field-specific errors and policy warnings. | M |
| US-012-T04 | Technical | Enforce policy in command and rollback services: Filter every operation payload and snapshot/restore image through active mapping policy; ignore/reject extra client fields. | API interception test proves unmapped field cannot be written or restored. | L |
| US-012-T05 | Testing | Test write/rollback boundary: Test allowed field update, blocked unmapped update, snapshot inclusion, rollback preservation of unrelated fields and policy changes across versions. | Automated tests prove field-scoped rollback only. | L |
| US-012-T06 | Documentation | Document field-governance and change procedure: Explain impact of changing writable/rollback flags and migration rules. | Administrators have an approved procedure for policy changes. | S |

### US-013 — As a board administrator, I want generated read-only runtime projection JSON so that runtime loading is efficient without creating a second editable configuration source.

**Priority / release:** P1 / V1  
**Phase:** Phase 1 — Configuration foundation  
**Dependencies:** US-010, US-011, US-012, US-002  
**Primary risk:** Stale projection causes runtime/configuration mismatch  
**Traceability:** FR-CFG-002; DM  
**Acceptance outcome:** Projection source hash/version created after validation; manual JSON edit is not offered; stale projection blocks runtime.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-013-T01 | Technical | Define runtime projection schema: Define generated read-only projection contract, version, source hash, payload minimisation and cache invalidation semantics. | Projection schema is versioned, documented and contains no secrets. | M |
| US-013-T02 | Technical | Implement projection generator: Generate projection only from validated normalized configuration and persist generation status, timestamp, source hash and product/schema versions. | Generator is idempotent and cannot create projection for invalid version. | L |
| US-013-T03 | Validation | Detect stale or incompatible projections: Compare source hash/version at load and block runtime when projection is missing, stale or incompatible. | Runtime fails closed with administrator-safe diagnostic code. | M |
| US-013-T04 | UX | Expose projection health: Show generated time, source hash, validation state, regeneration action and warnings in configuration administration. | Admin can resolve stale projection without manual JSON editing. | M |
| US-013-T05 | Testing | Test projection integrity and cache keys: Cover source change invalidation, hash mismatch, invalid JSON generation, cache separation by board/timezone/filter and older projection compatibility. | Automated tests prove projection cannot become an editable second source of truth. | L |
| US-013-T06 | Deployment | Package projection regeneration on import/upgrade: Run or queue validation/projection generation in controlled post-import steps and document operational ownership. | Import/release rehearsal results in valid active projections or a clear blocked state. | M |

### US-014 — As a Configuration Administrator, I want a guided Planora Configuration Studio PCF so that I can create, edit, validate, preview, version and activate Schedule Board configurations without manually maintaining interdependent ccsb_* records.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Configuration experience  
**Dependencies:** US-010, US-011, US-012, US-013, US-020, US-021, US-022, US-070, US-071  
**Primary risk:** Configuration PCF duplicates or bypasses the authoritative configuration lifecycle, metadata validation or security boundary  
**Traceability:** FR-CFG-001..010; FR-SEC-001/002; FR-API-001; NFR-UX-001/002; NFR-MNT-001; NFR-ALM-001  
**Acceptance outcome:** A Configuration Administrator can author draft versions through metadata-aware screens; active versions remain immutable; configuration validation, projection generation and activation use governed APIs; model-driven forms remain the support and low-level administration fallback.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-014-T01 | Functional | Define Configuration Studio PCF boundary and interaction specification: Define the Configuration Studio information architecture, navigation, authority split and interaction rules. Confirm that normalized ccsb_* configuration records remain authoritative; the PCF orchestrates draft authoring and governed APIs, while model-driven forms remain the support fallback. | Approved UX and architecture specification identifies all workbench sections, draft/active restrictions, validation behavior, error states, accessibility paths and the explicit no-direct-write boundary. | M |
| US-014-T02 | Technical | Create Planora Configuration Studio PCF solution and host shell: Create the React + Fluent UI PCF control, manifest, solution registration and Custom Page or dedicated model-driven app host. Establish routed workbench navigation, loading/error boundaries, telemetry correlation and reusable Fluent UI primitives. | The PCF is solution-aware, opens in the intended host, receives board/version context, exposes accessible navigation and has no direct configuration-table mutation implementation. | L |
| US-014-T03 | Technical | Implement configuration session, draft state and lifecycle command facade: Build the typed client facade for board/version selection, create draft, clone, compare, save draft changes and refresh. Use server APIs/services, ETag or row-version concurrency, correlation IDs and lifecycle policy from US-010. | The studio can create, select and clone a draft, detect concurrent changes, prevent direct edits to active versions and display server-authoritative lifecycle outcomes. | L |
| US-014-T04 | Technical | Build metadata discovery and mapping designer: Use the approved metadata service to present supported Dataverse tables, fields, choices and relationships. Implement entity, field and relationship mapping editors with semantic mapping keys, type compatibility feedback, write/rollback field policies and relationship-path previews. | Administrators can configure only live supported metadata; invalid logical names, missing fields, incompatible types, unsupported source tables and invalid graph relationships are blocked before activation. | XL |
| US-014-T05 | UX | Implement grouping, roles, capability and requirement configuration modules: Create guided editors for one-to-five grouping levels, fallback labels and resolver choice; named resource roles; capability criteria; quantity/capacity requirements; and previews of resolved resource paths and eligibility. | The workbench saves draft configuration through governed services and shows validation-ready group-path, role and requirement outcomes without allowing multi-path or unsupported resolver patterns. | L |
| US-014-T06 | UX | Implement status, rule and permission configuration modules: Create status-model and transition editors for booking, activity and assignment scopes; deterministic rule editors; permission-profile assignment screens; and previews of allowed actions and policy impact. | Only configured legal transitions, approved resolver contracts and additive CCSB restrictions can be saved; the studio never claims to grant access beyond Dataverse privileges. | L |
| US-014-T07 | Validation | Implement compare, validate, projection and activation workbench: Build the guided validation surface that runs ValidateBoardVersion, groups blocking, warning and information results, links findings to the relevant editor, presents a version comparison, requests projection generation and activates only validated drafts through governed APIs. | An administrator can resolve validation findings, regenerate a read-only projection, compare versions and activate a draft only when the server confirms compatibility and no blockers remain. | XL |
| US-014-T08 | Security | Enforce Configuration Studio authorisation, concurrency and audit policy: Apply action permissions, Dataverse row and field access, field-security treatment, optimistic concurrency, correlation and audit evidence to every studio command and diagnostic view. Redact sensitive metadata and policy values where required. | Configuration Administrator, Scheduler, Publish Manager, Support Analyst and unauthorised-user tests prove that the PCF neither overgrants data access nor bypasses lifecycle, audit or field-security controls. | L |
| US-014-T09 | Testing | Complete Configuration Studio component, integration and accessibility tests: Create unit and component tests for editors and navigation; integration tests against a Dataverse test environment for metadata, lifecycle, validation and activation; negative security tests; and keyboard and screen-reader tests for all configuration workflows. | Automated and manual evidence covers create, clone, edit, compare, validate, project and activate, invalid metadata, stale draft, permission denial and keyboard-only administration. | XL |
| US-014-T10 | Performance | Validate metadata and draft-editor performance at enterprise configuration scale: Measure metadata load, editor navigation, mapping-grid rendering, validation result rendering and draft-save latency against representative Dataverse metadata volumes; bound client caching and cancel obsolete requests. | Performance budgets, cancellation behavior and large-metadata test evidence are documented; no editor requests all environment records or blocks the UI without feedback. | M |
| US-014-T11 | Deployment | Package Configuration Studio, support fallback and administrator guidance: Package PCF assets, host page, roles, forms and view links and feature settings in the managed solution. Document install, role assignment, operational use, support fallback through model-driven forms and the limitations of V1 export and import. | Clean install and upgrade prove the studio loads with authorised access; release notes and support guidance explain how it coexists with model-driven administration and configuration promotion controls. | M |


## E03 - Resource, grouping and capacity configuration

### US-020 — As a board administrator, I want to define one to five resource grouping levels so that dispatchers can view the operating hierarchy.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Grouping/capacity foundation  
**Dependencies:** US-004, US-011  
**Primary risk:** Grouping complexity or unsafe resolver behavior  
**Traceability:** FR-CFG-004; FR-GRP-001  
**Acceptance outcome:** Direct field, lookup path and governed resolver options; levels are ordered; fallback label supported.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-020-T01 | Data | Implement group-definition schema: Create ordered levels 1–5 with resolver type, source field/lookup/resolver reference, display/sort/fallback/aggregate configuration. | Schema prevents duplicate level order and unsupported resolver configuration. | M |
| US-020-T02 | Functional | Implement grouping configuration behavior: Support direct resource fields, one lookup path and governed Custom API resolver type; retain a clear fallback label for null values. | A draft can define 1–5 ordered levels and preview expected path labels. | L |
| US-020-T03 | UX | Build grouping editor and preview: Provide level reorder, resolver-specific fields, metadata assistance, fallback label, sample-resource preview and warning for high-complexity hierarchy. | Admin can configure a group path without raw query authoring. | L |
| US-020-T04 | Validation | Validate resolver safety and hierarchy limits: Check valid source paths, maximum one lookup path, ordered levels, resolver registration/version and no multi-path configuration. | Invalid/ambiguous config blocks activation with diagnostic code. | L |
| US-020-T05 | Technical | Create group-path query/resolver contract: Implement deterministic resolver interface, server-side execution boundary, caching keys and safe timeouts for approved resolvers. | Resolver outputs one normalized path object per resource and cannot execute arbitrary runtime code. | L |
| US-020-T06 | Testing | Test grouping variants and null/fallback cases: Cover 1, 3 and 5 levels; direct fields; lookup path; approved resolver; null values; sort ordering; performance at reference page size. | Tests prove stable ordering and no duplicate path rendering. | L |
| US-020-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-021 — As a board administrator, I want each resource to resolve to one stable group path so that events and capacity do not duplicate across branches.

**Priority / release:** P1 / V1  
**Phase:** Phase 1 — Grouping/capacity foundation  
**Dependencies:** US-020  
**Primary risk:** Duplicate resource paths distort visibility/capacity  
**Traceability:** FR-GRP-001  
**Acceptance outcome:** Validation detects ambiguous/multiple paths; runtime shows a single path per board version.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-021-T01 | Technical | Define stable group-path resolution algorithm: Resolve exactly one ordered segment list and deterministic fallback for each resource/board-version pair. | Same input and version always returns identical canonical path. | M |
| US-021-T02 | Validation | Detect ambiguity and multi-path output: Validate resolver outputs, lookup joins and null fallback rules; reject any resource that resolves to more than one path. | Configuration validation reports affected resource samples and root cause. | M |
| US-021-T03 | Data | Persist/cache path identity safely: Define ephemeral/read-cache or materialized path policy with board version, resource ID and resolver version keys; avoid stale path reuse. | Cache invalidates on mapping/version/resource changes. | M |
| US-021-T04 | UX | Surface path diagnostics: Show resolved path and ambiguous-path errors in admin preview and resource details. | Admin can inspect why a resource is placed in a group. | S |
| US-021-T05 | Testing | Test determinism and non-duplication: Run data sets with duplicate values, missing lookups, changed resources and resolver failures. | Automated tests confirm exactly one visible placement per resource. | M |
| US-021-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-022 — As a board administrator, I want named resource roles and requirements so that group bookings can demand the right people, vehicles, rooms or equipment.

**Priority / release:** P0 / V1  
**Phase:** Phase 1 — Grouping/capacity foundation  
**Dependencies:** US-004, US-011  
**Primary risk:** Incorrect role/capacity calculation compromises operations  
**Traceability:** FR-CFG-006; FR-GPH-004  
**Acceptance outcome:** Roles can restrict type/capability; requirement stores quantity/capacity; validation supports partial fill.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-022-T01 | Data | Implement roles and requirements model: Create roles, resource-type restrictions, capability criteria, quantity/capacity fields, min/max semantics and eligible assignment statuses. | Role/requirement data supports multiple requirements per activity and partial completion. | L |
| US-022-T02 | Functional | Build role and requirement configuration: Allow administrators to define named roles, capacity semantics, compatible resource types/capabilities and publish-blocking policy. | Configured role/restriction is available to validation and runtime forms. | L |
| US-022-T03 | UX | Design requirement editing and summary: Provide accessible forms to add/edit requirements and a clear summary of demand, allocation, shortfall and over-allocation. | Users can understand requirement state without relying on colour. | M |
| US-022-T04 | Technical | Create eligibility and allocation calculator: Implement deterministic calculation for role compatibility, eligible status contribution, allocated quantity/capacity, partial fill and over-allocation. | Calculator is shared by validation, board rendering, workbenches and publish checks. | L |
| US-022-T05 | Validation | Enforce role and capacity policy: Validate incompatible resource type/capability, invalid allocation values, duplicate prohibited roles and policy-required coverage. | API returns warning/block with requirement context and possible action. | L |
| US-022-T06 | Testing | Test multi-resource and capacity scenarios: Cover quantity-only, capacity-only, mixed roles, partial fill, status exclusion, over-allocation and resource capability expiry. | Reference test suite produces known completion result for each scenario. | L |
| US-022-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E04 - Runtime workspace and read model

### US-029 — As a scheduler, I want the Planora Schedule Board Runtime PCF and Projection Controller to resolve an active, validated board projection, compose the operational workspace and route all actions through governed APIs so that the board is fast, safe and consistent.

**Priority / release:** P0 / V1  
**Phase:** Phase 2 — Runtime PCF foundation  
**Dependencies:** US-001, US-003, US-013, US-070, US-071  
**Primary risk:** Runtime PCF becomes an ungoverned second business-logic layer or presents stale data after a command  
**Traceability:** FR-ACC-001/003; FR-WSP-001..005; FR-OPS-002; NFR-PER-001/002/007; NFR-SEC-003; NFR-MNT-001  
**Acceptance outcome:** The Runtime PCF loads only active validated compatible projections, fails closed for missing/stale/incompatible projection, performs visible-slice reads, routes all mutations through Custom APIs, refreshes only affected scope and does not directly write schedule, configuration or control records.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-029-T01 | Technical | Define Runtime PCF and Projection Controller boundary: Define the runtime composition contract: PCF host lifecycle, board bootstrap, projection controller, read-model query client, command client, cache keys, targeted refresh scope and explicit prohibition on direct schedule, configuration or control-table writes. | Approved runtime boundary specifies what US-029 owns and what remains in US-030–US-033, US-040–US-063 and the Custom API layer; DTOs, state transitions and error modes are versioned. | M |
| US-029-T02 | Technical | Create Planora Schedule Board Runtime PCF and model-driven host shell: Create the React + Fluent UI PCF project, manifest, solution component, model-driven host integration, context inputs, theme lifecycle, error boundary and feature-safe loading shell. | The PCF is deployed through the managed solution, receives host context, emits correlation IDs and displays accessible loading, no-access and fatal-error states without direct data mutation code. | L |
| US-029-T03 | Technical | Implement active board projection bootstrap and fail-closed controller: Resolve board context, active version, compatibility status and read-only runtime projection. Validate projection schema version and source hash; reject missing, stale, incompatible or unauthorised board contexts with support-safe diagnostics. | The runtime starts only for an active validated compatible board projection; every failed state provides a correlation ID and clear administrator remediation without querying schedule data. | L |
| US-029-T04 | Technical | Implement visible-slice read client, cache and obsolete-request cancellation: Implement the typed read client for resource and group pages, assignment occurrences, overlays and detail slices using projection mappings. Use stable cache keys, request cancellation, request identity checks and bounded payload selection. | The PCF retrieves only visible and overscan data for the selected board, version, timezone, filter and range, ignores obsolete responses and exposes deterministic loading, error and empty states. | XL |
| US-029-T05 | Technical | Build runtime state composition and region integration contract: Implement shared state for board context, date range, scale, selection, details, workbench state, query results and permission-aware command availability. Establish composition slots for the command bar, tree/timeline, details and workbench. | US-030–US-033 and US-040–US-063 can plug into one typed runtime state contract without duplicating board bootstrap, security, cache or selected-context logic. | L |
| US-029-T06 | Functional | Implement governed command adapter and proposal state handling: Create the reusable client adapter that submits validation, warning confirmation, execute, publish and rollback requests through versioned Custom APIs. Manage operation correlation, idempotency, row versions, confirmation expiry, pending UI state and safe rollback of optimistic previews. | No runtime interaction can call direct Dataverse CRUD for schedule, configuration or control records; all command outcomes are typed, correlated and handed to the appropriate existing feature story. | XL |
| US-029-T07 | Technical | Implement targeted refresh and result reconciliation controller: Consume affected resource, date and group scope returned by APIs, invalidate only relevant cache keys, reconcile selection, details and workbench state and avoid discarding unrelated user context after success, warning, stale or failure outcomes. | A committed command refreshes only the server-returned slice; stale, blocked and failure states restore authoritative data and never leave ghost events, stale locks or false success state. | L |
| US-029-T08 | Security | Add runtime security, telemetry and support-safe diagnostics: Apply permission-aware reads and actions, redacted errors, correlation propagation, safe telemetry, browser-log suppression and support diagnostic links. Ensure the projection and read model contain no secrets or unauthorised sensitive content. | Security and observability tests confirm that the runtime respects Dataverse plus CCSB restrictions, exposes no protected data through client logs or telemetry and supports end-to-end correlation. | L |
| US-029-T09 | Testing | Complete Runtime PCF contract, integration, performance and accessibility tests: Create component and integration tests for projection bootstrap, fail-closed paths, cache cancellation, command adapter, targeted refresh, security scopes, keyboard flow, screen-reader states and reference performance instrumentation. | Evidence covers missing, stale and incompatible projections, forged board context, obsolete requests, command failure and stale response, targeted refresh, keyboard-only use and performance budgets for the runtime shell. | XL |
| US-029-T10 | Deployment | Package Runtime PCF, host integration and operational support guidance: Package PCF, host configuration, roles, environment settings and diagnostic links. Document deployment, version compatibility, projection failure triage, supported browser and host assumptions, rollback limits and ownership of subsequent runtime feature modules. | Clean install and upgrade rehearsal prove the Runtime PCF loads only validated projections; release and support material states its API-only mutation boundary and the dependencies of US-030–US-063. | M |


### US-030 — As a scheduler, I want to select a permitted board and date range so that I can work in the correct operational context.

**Priority / release:** P0 / V1  
**Phase:** Phase 2 — Read workspace  
**Dependencies:** US-003, US-013, US-070  
**Primary risk:** Invalid board context or timezone misinterpretation  
**Traceability:** FR-ACC-002; FR-WSP-001  
**Acceptance outcome:** Only allowed boards show; active validated version loads; date navigation uses board timezone.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-030-T01 | Technical | Implement board-context bootstrap: Resolve current user context, permitted boards, active validated version, projection, canonical timezone and initial date range. | Bootstrap returns a typed context or a fail-closed state with correlation ID. | L |
| US-030-T02 | UX | Build workspace command bar: Implement accessible board selector, date navigation, date-range display, scale/view selector, refresh and contextual loading/error states. | Core context can be changed via keyboard and screen reader without drag interaction. | L |
| US-030-T03 | Functional | Implement timezone-safe navigation: Calculate today, prior/next range and calendar labels using board IANA timezone and retain UTC query boundaries. | Date navigation remains correct across DST transitions and user locale differences. | M |
| US-030-T04 | Security | Apply permitted-board filtering: Enforce board/action permissions before rendering selector values or querying schedule data. | Forged board ID cannot load unauthorised context. | M |
| US-030-T05 | Validation | Fail closed on invalid board/version: Handle no permission, no board, retired board, invalid version and stale projection states with safe diagnostics. | Runtime never attempts schedule queries for invalid context. | M |
| US-030-T06 | Testing | Test context and timezone matrix: Cover multiple permitted boards, no-board user, retired/invalid version, locale/date boundary and DST days. | Automated UI/integration tests meet acceptance outcomes. | L |
| US-030-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-031 — As a scheduler, I want a virtualised group/resource timeline with server paging so that large schedules remain usable.

**Priority / release:** P0 / V1  
**Phase:** Phase 2 — Read workspace  
**Dependencies:** US-013, US-030  
**Primary risk:** Dense schedule performance and stale client data  
**Traceability:** FR-WSP-002; NFR-PER-001/002  
**Acceptance outcome:** Only current page/viewport data loaded; request cancellation works; performance baseline met.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-031-T01 | Technical | Implement read-model query contracts: Define server/Web API query shapes for group/resource pages, assignment occurrences, overlays, cursors and date/resource scope. | Contracts select only active mapped fields and carry continuation/refresh identifiers. | L |
| US-031-T02 | Technical | Build virtualised scheduler engine shell: Implement custom Fluent UI timeline grid, virtualised resource/group rows and timeline cells using TanStack Virtual; keep layout engine product-owned. | DOM count remains bounded at reference profile and scroll/selection are stable. | XL |
| US-031-T03 | Technical | Implement visible-slice cache and cancellation: Use cache keys for board version, timezone, filters, group path, resource cursor, date range and data shape; cancel/ignore obsolete requests. | Rapid navigation cannot paint stale responses over current context. | L |
| US-031-T04 | UX | Design progressive load and empty/error states: Retain current context during refresh, show loading feedback within 200 ms, indicate page boundaries and provide retry without data loss. | Users can distinguish loading, empty, permission and fault states. | M |
| US-031-T05 | Performance | Set performance budgets and instrumentation: Instrument load/render/query/scroll timings and payload/DOM counts for NFR reference profile. | Dashboard reports p95 shell, slice refresh, preview and API timing metrics. | L |
| US-031-T06 | Testing | Run viewport/paging/performance tests: Test resource page boundaries, overscan, event density, request cancellation, 5,000 working-set occurrences and 20-user reference load. | Performance evidence meets NFR-PER-001/002 before progression. | XL |
| US-031-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-032 — As a scheduler, I want search, filters and saved non-sensitive preferences so that I can repeatedly focus on my work.

**Priority / release:** P1 / V1  
**Phase:** Phase 2 — Read workspace  
**Dependencies:** US-030, US-031  
**Primary risk:** Unsafe filters/preferences leak or corrupt user context  
**Traceability:** FR-WSP-001/003  
**Acceptance outcome:** Filter changes refresh correct slice; preference respects permissions/policy.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-032-T01 | Data | Define filter and preference model: Define configured filter fields/operators, saved preference scope, policy/retention and sensitive-data exclusion. | Preferences contain no schedule content or secrets and are isolated by user/board. | M |
| US-032-T02 | Functional | Implement filter/search query composition: Build typed resource, group, status, date and configured filter composition against active mappings and visibility rules. | Filter changes update only relevant board slice and retain valid selections. | L |
| US-032-T03 | UX | Build accessible search/filter experience: Provide debounced search, filter chips, clear/reset, selected-state summary, keyboard access and meaningful no-result message. | All filters are operable without pointer-only controls. | L |
| US-032-T04 | Technical | Persist safe user preferences: Store selected board, scale/view, filters and collapsed groups only where policy allows; version/validate preference payload. | Invalid/stale preference is ignored safely and does not prevent board load. | M |
| US-032-T05 | Validation | Validate configured filters: Reject unapproved mapped fields/operators and prevent query expansion beyond visibility/permission scope. | Server/client contract tests prove no arbitrary filter injection/path. | M |
| US-032-T06 | Testing | Test search, persistence and permission cases: Cover restore/reset, changed configuration, special characters, no results, inaccessible filter values and performance under repeated changes. | Tests validate correct slice and no leakage. | L |
| US-032-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-033 — As a scheduler, I want overlays for availability, leave, work hours and holidays so that I can make safe scheduling choices.

**Priority / release:** P1 / V1  
**Phase:** Phase 2 — Read workspace  
**Dependencies:** US-011, US-013, US-031  
**Primary risk:** Incorrect overlay time interpretation creates unsafe choices  
**Traceability:** FR-CNF-001; NFR-UX-004  
**Acceptance outcome:** Configured overlays appear; missing mappings degrade safely; non-colour cues provided.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-033-T01 | Data | Define overlay mapping semantics: Model optional Availability, Leave, Work-hours and Public-holiday definitions, UTC/date fields, timezone interpretation, display labels and precedence. | Each overlay type is either fully mapped/validated or safely unavailable. | M |
| US-033-T02 | Technical | Implement overlay read and layout engine: Query overlays only for visible resource/date scope and render non-interactive/interactive semantics consistently with timeline slots. | Overlay data is range-bounded, virtualised and layered deterministically. | L |
| US-033-T03 | UX | Design overlay legend and non-colour cues: Provide legend, patterns/icons/text labels, focus/tooltip details and panel toggle behavior. | Users can identify every overlay state without colour perception. | M |
| US-033-T04 | Validation | Validate optional mapping and precedence: Handle missing mapping, invalid date range, unavailable resource field and overlapping overlay precedence without failing the board. | Diagnostics identify disabled overlay and runtime retains core schedule view. | M |
| US-033-T05 | Testing | Test timezone, DST and overlap cases: Cover whole-day/partial intervals, holidays across timezone boundary, resource-specific leave, multiple overlays and missing configuration. | Automated tests verify correct interval projection and safe degradation. | L |
| US-033-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E05 - Schedule graph operations

### US-040 — As a scheduler, I want to create or edit a booking/activity with its own time so that I can schedule the actual work rather than only a parent record.

**Priority / release:** P0 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-011, US-012, US-071, US-070  
**Primary risk:** Customer data mutation rules are incomplete  
**Traceability:** FR-GPH-002; FR-OPS-004  
**Acceptance outcome:** Activity start/end independent; invalid interval rejected; parent context retained.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-040-T01 | Functional | Define create/edit operation semantics: Specify which booking/activity fields can be created/edited, parent linkage rules, default values, independent activity times and unscheduled state. | Operation contract is approved for both mapped and optional native graph modes. | L |
| US-040-T02 | UX | Build accessible booking/activity forms: Create details-panel/modal forms for create/edit with parent context, start/end controls, validation summary, confirmation and cancellation behavior. | Every field-level and cross-field error is keyboard/screen-reader accessible. | L |
| US-040-T03 | Technical | Implement validate/execute handling: Compose graph delta and row versions; call validation then execute API; process pass/warn/block/stale outcomes and targeted refresh. | Client performs no direct CRUD and restores UI on rejected command. | L |
| US-040-T04 | Data | Map defaults and managed fields: Use active mapping to resolve source entity/fields, values, status/default policy and required relationship fields. | Only mapped writable fields reach server command. | M |
| US-040-T05 | Validation | Enforce interval and parent rules: Validate start < end, timezone/DST behavior, parent/child relationship, configured status and protected lock scope. | Invalid activity cannot be created/edited and explanation identifies exact affected record. | L |
| US-040-T06 | Testing | Test create/edit paths: Cover native/mapped graph, independent child time, invalid interval, warning confirmation, stale parent, denied access and locked scope. | API/UI integration tests produce audit and affected-scope evidence. | L |
| US-040-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-041 — As a scheduler, I want to assign one or more resources to an activity with roles so that group work is represented accurately.

**Priority / release:** P0 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-040, US-022, US-071  
**Primary risk:** Invalid resource allocation or duplicate assignment  
**Traceability:** FR-GPH-003; FR-OPS-004  
**Acceptance outcome:** One activity supports multiple assignments; role compatibility validated; parent/sibling context visible.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-041-T01 | Functional | Define assign/unassign/reassign semantics: Specify assignment create/remove/reassign behavior, role selection, inherited time, allocation values and requirement impact. | Operation contract identifies graph delta and lifecycle effects for each action. | L |
| US-041-T02 | UX | Build assignment controls: Provide accessible form, resource-picker, role picker, capacity/quantity fields, candidate eligibility explanation and sibling context. | User can assign multiple resources without relying on drag/drop. | L |
| US-041-T03 | Technical | Implement assignment command handlers: Create typed client/server handling for assign/unassign/reassign using idempotency, row versions and affected-scope return. | Duplicate/retried command cannot create duplicate assignment. | L |
| US-041-T04 | Data | Resolve resource, role and activity mapping: Use active mappings for assignment/resource role fields and native/mapped relationships. | Server rejects source entity/field outside active board mapping. | M |
| US-041-T05 | Validation | Validate eligibility and capacity: Run role/type/capability, availability, overlap, allocation, lock and status checks before commit. | Warning/block response includes role/requirement/resource context. | L |
| US-041-T06 | Testing | Test group-work cases: Cover multi-resource assignment, partial completion, incompatible role, zero/over capacity, duplicate assignment, unassign and stale concurrency. | Tests verify correct requirement calculations and audit outcome. | L |
| US-041-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-042 — As a scheduler, I want to move, resize and reassign activities/assignments so that schedule changes are controlled and explained.

**Priority / release:** P0 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-040, US-041, US-051, US-071  
**Primary risk:** Non-atomic move/resize/reassign or concurrency loss  
**Traceability:** FR-OPS-001/005/007  
**Acceptance outcome:** Validate first; warn/confirm; execute with row version; affected scope refreshes.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-042-T01 | Functional | Define move/resize/reassign delta rules: Specify whether action affects activity, selected assignment override or all child assignments; define snapping, time boundaries and reassignment semantics. | Each gesture/form action has deterministic graph delta and refresh scope. | L |
| US-042-T02 | UX | Implement drag, resize and form alternatives: Use dnd-kit for input/sensors and product-owned hit testing; add explicit Move, Resize and Reassign forms; show preview and warning confirmation. | Keyboard/form path achieves same supported result as pointer action. | XL |
| US-042-T03 | Technical | Implement validate-confirm-execute orchestration: Call ValidateScheduleOperation, handle confirmation token expiry, execute idempotently, and refresh returned resource/date/group slices. | No mutation is sent without valid context, correlation, row versions and token when required. | L |
| US-042-T04 | Validation | Evaluate affected graph and locks: Validate all affected activity/assignment/resource intervals, availability/overlaps, capacity, rules, status, protected scopes and stale rows. | Server returns pass/warn/block with actionable code and all affected scope. | XL |
| US-042-T05 | Testing | Test mutation, warning and stale paths: Cover move/resize across DST, multiresource activity, warning confirmation, blocked leave/lock, double-submit, stale row and partial failure. | Automated integration tests verify atomicity and targeted refresh. | XL |
| US-042-T06 | Observability | Record operation evidence: Record command intent, result, affected records, rules, confirmation, correlation/idempotency, actor and performance timings. | Support trace can reconstruct outcome without sensitive client log content. | M |
| US-042-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-043 — As a scheduler, I want an assignment time override when the board permits it so that a resource can be scheduled for a portion of the activity.

**Priority / release:** P1 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-041, US-042  
**Primary risk:** Override semantics diverge from activity schedule  
**Traceability:** FR-GPH-006  
**Acceptance outcome:** Override only appears when configured; rules enforce allowed boundary; inherited time remains default.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-043-T01 | Data | Add override mapping/policy: Define optional assignment start/end override mappings and feature flag; default to inherited activity interval. | Board version without both fields/policy cannot enable override. | M |
| US-043-T02 | Functional | Define override lifecycle: Specify create/edit/clear override, display behavior, interaction with move/resize and inheritance after activity time changes. | Behavior is deterministic for parent time update and assignment override removal. | M |
| US-043-T03 | UX | Provide override form and visual marker: Expose override controls only when permitted, show inherited versus overridden time and provide reset-to-activity action. | Users can clearly distinguish override from inherited interval. | M |
| US-043-T04 | Validation | Validate override boundaries: Apply configured rule for permitted bounds, availability/overlap/capacity and protected scope effects. | Invalid override returns field-level and rule-level explanation. | M |
| US-043-T05 | Testing | Test override permutations: Cover disabled feature, partial activity interval, reset behavior, parent move/resize, DST and rollback-managed scope. | Tests prove default inheritance remains unchanged when override unavailable. | M |
| US-043-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-044 — As a scheduler, I want distinct booking, activity and assignment status transitions so that operational state is accurate at the right level.

**Priority / release:** P1 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-010, US-011, US-071  
**Primary risk:** Status transition bypass or incorrect side effect  
**Traceability:** FR-CFG-005; FR-OPS-007  
**Acceptance outcome:** Independent configured transitions; forbidden transitions rejected; history audited.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-044-T01 | Data | Implement status models and transitions: Create scope-specific Booking, Activity and Assignment status values, colors, eligible-for-capacity flags and permitted transition records. | Status models can be independently enabled per board version. | L |
| US-044-T02 | Functional | Define transition policy: Specify transition triggers, required reason, permission, side effects, publish/lock policy and terminal status behavior. | Policy is deterministic and documented per scope. | M |
| US-044-T03 | UX | Build status action experience: Provide accessible status menu/form, current state, permitted transitions, reason input, invalid-state explanation and non-colour indicators. | Forbidden transitions are not presented as executable actions. | M |
| US-044-T04 | Technical | Enforce transitions in command service: Validate source/target status, action permission, mapping value, row version and side-effect rules on server. | Direct write to status field outside command contract is rejected. | L |
| US-044-T05 | Testing | Test independent status state machines: Cover allowed/forbidden transition, each scope, required reason, capacity contribution change, lock/stale handling and audit history. | Automated tests prove independent scopes do not incorrectly cascade. | L |
| US-044-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E06 - Requirements, conflicts and unscheduled work

### US-050 — As a scheduler, I want required versus allocated quantity/capacity for an activity so that I can see whether group work is complete.

**Priority / release:** P0 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-022, US-041  
**Primary risk:** Incorrect capacity/quantity state  
**Traceability:** FR-GPH-007; FR-UNS-002  
**Acceptance outcome:** Eligible assignment statuses count correctly; shortfall/over-allocation displayed with text/icon.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-050-T01 | Data | Define completion and allocation measures: Define required quantity/capacity, allocation contribution, eligible status, role/type matching and over-allocation formulas. | Formulas are documented and reused across board, publish and workbench. | M |
| US-050-T02 | Technical | Implement shared requirement calculator: Implement deterministic aggregate calculator for activity requirements and assignments, including partial, filled, shortfall and over-allocated states. | Calculator produces consistent result for API and UI inputs. | L |
| US-050-T03 | UX | Render accessible allocation indicators: Show required/allocated/remaining values, status text/icon, detailed breakdown and parent/activity context in board and details. | State is comprehensible without colour and has a screen-reader label. | M |
| US-050-T04 | Validation | Apply coverage rules: Evaluate required coverage at configured operation/publish triggers and return warning/block according to board policy. | Unfilled/overallocated requirement has explicit policy outcome. | M |
| US-050-T05 | Testing | Test calculation matrix: Test no requirement, quantity/capacity, multiple roles, partial fills, status exclusion, resource type mismatch and zero/negative input. | Results match approved example matrix. | L |
| US-050-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-051 — As a scheduler, I want blocking and warning conflicts explained before commit so that I can decide safely.

**Priority / release:** P0 / V1  
**Phase:** Phase 3 — Core command runtime  
**Dependencies:** US-022, US-070, US-071  
**Primary risk:** Rules are bypassed or not explainable  
**Traceability:** FR-CNF-002; FR-OPS-001  
**Acceptance outcome:** Rule, severity, scope and message returned; warning needs confirmation when configured.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-051-T01 | Data | Define rule outcome contract: Standardize pass/warn/block, rule ID/version, scope, severity, explanation, suggested action and confirmation requirements. | All rule resolvers emit typed, localized-safe result objects. | M |
| US-051-T02 | Technical | Implement rule pipeline: Implement ordered deterministic evaluation for built-in availability, overlap, capacity, role, lock, status and approved resolver rules. | Pipeline is invoked consistently by validate, execute and publish. | XL |
| US-051-T03 | UX | Build conflict and confirmation dialog: Display affected booking/activity/assignment/resource context, plain-language reason, warning acknowledgement/reason and safe alternatives. | Users cannot mistake warning for success or block for a transient load error. | L |
| US-051-T04 | Validation | Secure confirmation tokens: Issue short-lived confirmation token bound to user, board/version, proposal hash and rule outcomes; revalidate before execute. | Modified/expired/replayed token is rejected. | L |
| US-051-T05 | Testing | Test pass/warn/block behavior: Cover ordering, multiple rules, warning acceptance/rejection, blocked action, resolver timeout/error and rule changes after validation. | Tests prove no warning bypass and no stale confirmation execution. | L |
| US-051-T06 | Observability | Capture rule diagnostics: Record rule code, timing, safe scope counts and outcome without leaking protected schedule content. | Support analyst can correlate decision to rule version and operation. | M |
| US-051-T07 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-052 — As a scheduler, I want a conflict workbench so that I can triage unresolved issues without losing timeline context.

**Priority / release:** P1 / V1  
**Phase:** Phase 4 — Operational workbenches  
**Dependencies:** US-051, US-072  
**Primary risk:** Conflict history/action permissions are incorrect  
**Traceability:** FR-CNF-003/004  
**Acceptance outcome:** Filter/sort/select; history retained; actions permission controlled.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-052-T01 | Data | Model persistent conflict cases: Implement conflict case fields for rule/version, severity, source scope, operation, status, acknowledgement/resolution, actor, reason and timestamps. | Resolved history is retained and linked to original operation. | L |
| US-052-T02 | Technical | Create conflict read/query service: Expose permission-filtered, paged conflict list/detail queries with stable sort/filter/search and board/version scope. | Query returns no conflict outside caller access and supports correlation links. | M |
| US-052-T03 | UX | Build conflict workbench: Provide list, filters, sort, severity/status indicators, context preview, deep link to timeline, resolution actions and retained selection. | Scheduler can triage conflict without losing timeline context. | L |
| US-052-T04 | Functional | Implement resolution action policy: Define acknowledge, accept warning, override where allowed, revalidate, reopen and close semantics with reasons and permissions. | Each resolution action is server-authorized and auditable. | M |
| US-052-T05 | Testing | Test conflict lifecycle and access: Cover unresolved/resolved/reopened, pagination, permission denial, linked record deleted/changed, stale conflict and concurrent resolution. | History remains immutable and UI handles unavailable source record safely. | L |
| US-052-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-053 — As a scheduler, I want an unscheduled/partial workbench so that I can fill unassigned activities and incomplete requirements.

**Priority / release:** P1 / V1  
**Phase:** Phase 4 — Operational workbenches  
**Dependencies:** US-050, US-041, US-031  
**Primary risk:** Unscheduled work becomes stale or unauthorised  
**Traceability:** FR-UNS-001  
**Acceptance outcome:** Shows configured unassigned/partial work; open/assign actions available.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-053-T01 | Data | Define unscheduled/partial query criteria: Translate configured unassigned activity, incomplete requirement, optional status and visibility rules into bounded read criteria. | Criteria are traceable to active board version and exclude unauthorised records. | M |
| US-053-T02 | Technical | Build workbench read model: Implement paged, filtered workbench query with requirement summaries, parent context, existing assignments and target refresh scope. | Results remain current after operation/publish without full board reload. | L |
| US-053-T03 | UX | Build unscheduled/partial workbench: Provide list, filters, shortfall labels, details, quick assign/open actions and accessible empty/loading/error states. | Scheduler can identify and open a work item with keyboard only. | L |
| US-053-T04 | Functional | Connect workbench to assignment flow: Pass correct activity/requirement context into Assign and candidate selection; retain return context after commit. | Successful assignment updates workbench state and affected timeline slice. | M |
| US-053-T05 | Testing | Test state changes and security: Cover unassigned, partial, filled, overallocated, cancelled/ignored status, filter changes, permission and concurrent assignment. | No stale/orphaned work item survives refresh. | L |
| US-053-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E07 - Publish, locks and rollback

### US-060 — As a publish manager, I want to preview the resolved publish scope and blockers so that I do not publish an unsafe schedule.

**Priority / release:** P0 / V1  
**Phase:** Phase 4 — Publish governance  
**Dependencies:** US-012, US-051, US-070, US-071  
**Primary risk:** Publish preview differs from actual scope  
**Traceability:** FR-PUB-001/002/003  
**Acceptance outcome:** Scope, counts, warning/block, pending changes and lock policy displayed; server revalidates.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-060-T01 | Functional | Define publish-scope resolution policy: Specify inputs, allowed group/resource filters, UTC boundaries, pending-change inclusion, lock policy, warning/block policy and no-op behavior. | Server owns final resolved scope and policy is versioned. | L |
| US-060-T02 | Technical | Implement publish preview command: Create a read-only Custom API/endpoint that resolves scope, calculates counts, evaluates rules/locks and returns preview/correlation data. | Preview cannot mutate records and is repeatable for same inputs/version. | L |
| US-060-T03 | UX | Build publish-preview workflow: Provide date/scope selector, counts, pending changes, warnings/blockers, lock impact, confirmation/reason and explicit refresh state. | Publish manager understands exactly what will be published before commit. | L |
| US-060-T04 | Validation | Revalidate immediately before commit: Re-run authorisation, scope, lock, requirement, rule and row-version checks in publish transaction. | Changed/newly blocked scope cannot be published from stale preview. | L |
| US-060-T05 | Testing | Test preview and scope edge cases: Cover no records, filters, boundary times, partial lock, warning policy, new conflict after preview, permission and large scope pagination. | Tests prove preview is advisory and final decision remains server authoritative. | L |
| US-060-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-061 — As a publish manager, I want a successful publish to create immutable snapshots and locks so that official schedules are protected.

**Priority / release:** P0 / V1  
**Phase:** Phase 4 — Publish governance  
**Dependencies:** US-060, US-072  
**Primary risk:** Official schedule state is partially committed or mutable  
**Traceability:** FR-PUB-004/005  
**Acceptance outcome:** Header/items created; managed fields included; lock rules enforced; audit linked.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-061-T01 | Data | Implement immutable snapshot structure: Implement snapshot header/item data, resolved scope, managed field before/after images, source identity, hashes, predecessor and publish sequence. | Snapshot stores only explicitly rollback-managed fields and is append-only. | L |
| US-061-T02 | Technical | Implement transactional publish service: Within Custom API transaction, revalidate scope, create snapshot/items, create/update locks, mark schedule changes published, audit result and return affected scope. | Publish is atomic: failure leaves no successful snapshot/lock/change state. | XL |
| US-061-T03 | Security | Enforce publish and lock permissions: Check Dataverse and CCSB publish/override permission; require reason for overrides according to policy. | Unauthorised caller cannot publish or create lock through forged request. | M |
| US-061-T04 | UX | Show publish result and official state: Surface snapshot ID/time/actor, resulting locks, warnings and failed records with accessible summary. | User can navigate from result to snapshot/audit evidence. | M |
| US-061-T05 | Testing | Test snapshot/lock atomicity: Cover successful publish, transaction failure, lock conflict, managed-field images, repeated request/idempotency, partial scope and audit linkage. | Automated test proves no partial official state after fault. | XL |
| US-061-T06 | Deployment | Define snapshot retention and operational runbook: Set retention/access policy, purge approval process, monitoring checks and post-publish verification steps. | Operations can retain/recover evidence according to policy. | M |

### US-062 — As a publish manager, I want governed rollback to a compatible prior snapshot so that I can recover the published schedule without overwriting unrelated data.

**Priority / release:** P0 / V1  
**Phase:** Phase 4 — Publish governance  
**Dependencies:** US-061, US-012, US-072  
**Primary risk:** Rollback restores wrong scope or fields  
**Traceability:** FR-RBK-001..004  
**Acceptance outcome:** Reason/permission required; only rollback-managed fields restored; new audit/result snapshot created.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-062-T01 | Functional | Define compatible rollback policy: Specify snapshot eligibility, board/version compatibility, allowed sub-scope, dependency/lock checks, required reason and resulting publish state. | Policy explicitly excludes general database undo. | L |
| US-062-T02 | Technical | Implement field-scoped rollback transaction: Resolve snapshot items, compare current compatibility/row versions, restore only rollback-managed fields, write operation/change/audit and result snapshot. | Rollback is atomic and cannot mutate unmapped/unmanaged fields. | XL |
| US-062-T03 | UX | Build rollback preview and confirmation: Show target snapshot, planned records/fields, current conflicts/dependencies, reason capture and clear destructive-action messaging. | User can review impact and cannot execute without required permission/reason. | L |
| US-062-T04 | Validation | Protect against unsafe restoration: Check lock policy, snapshot compatibility, current record existence/state, changed dependencies and actor privileges before transaction. | Unsafe rollback returns explicit blocker/warning and changes nothing. | L |
| US-062-T05 | Testing | Test restoration boundaries: Cover allowed restoration, unrelated-field preservation, newer publish, deleted source record, lock override, stale rows, partial selection and result snapshot. | Tests prove rollback is limited and fully traceable. | XL |
| US-062-T06 | Documentation | Publish rollback runbook: Document when to use rollback, limitations, approvals, recovery from failed request and audit review. | Support/release owners can perform a controlled rehearsal. | M |

### US-063 — As a scheduler, I want lock state and pending-change state visible so that I understand why a change is blocked or not yet official.

**Priority / release:** P1 / V1  
**Phase:** Phase 4 — Publish governance  
**Dependencies:** US-060, US-061, US-031  
**Primary risk:** Lock state is ambiguous or stale in UI  
**Traceability:** FR-PUB-005; FR-UX-003  
**Acceptance outcome:** Timeline/details show lock/pending badges and text; policy displayed.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-063-T01 | Technical | Expose lock and pending-change read model: Return effective lock state/policy, pending status, snapshot reference and user-permitted actions with visible slices/details. | Read model uses server-evaluated scope; client does not infer lock from colour/state alone. | M |
| US-063-T02 | UX | Design status badges and explanatory details: Show lock/pending/official status using icon/text/badge, tooltip/details, next action and scope explanation. | State is accessible and visible in timeline, details and relevant workbenches. | M |
| US-063-T03 | Functional | Integrate state into action affordances: Disable or route operations based on server policy while retaining explicit form/action explanation and override workflow where permitted. | UI never implies an action will succeed when policy blocks it. | M |
| US-063-T04 | Testing | Test state visibility and refresh: Cover locked/unlocked/pending/published/rolled-back states, partial scopes, permission differences and operation-triggered refresh. | UI state matches server decision after every tested change. | M |
| US-063-T05 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E08 - Security, APIs, audit and support

### US-070 — As a security administrator, I want CCSB action permissions layered below Dataverse access so that the product does not overgrant customer data.

**Priority / release:** P0 / V1  
**Phase:** Phase 0 — Security foundation  
**Dependencies:** US-004  
**Primary risk:** CCSB overgrants access beyond Dataverse  
**Traceability:** FR-SEC-001/002; NFR-SEC-002  
**Acceptance outcome:** Permission cannot bypass Dataverse security; negative role tests pass.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-070-T01 | Security | Define permission model and matrix: Define CCSB actions, scope dimensions, least-privilege roles, relationship to Dataverse table/row/field security and negative cases. | Matrix is approved for admin, scheduler, publisher, support and unauthorised personas. | L |
| US-070-T02 | Data | Implement permission profiles and assignments: Create/secure ccsb_permissionprofile and assignment schema with board/group/role scope and allowed-operation flags. | Profiles only further restrict effective Dataverse access. | M |
| US-070-T03 | Technical | Build server-side authorisation service: Resolve caller identity, Dataverse privilege and CCSB action/scope before every command, configuration action and diagnostics call. | No client-supplied role/scope can elevate access. | L |
| US-070-T04 | UX | Design permission-aware actions: Hide unavailable actions where appropriate, keep non-disclosing disabled state/diagnostics, and avoid revealing inaccessible record content. | UI follows least disclosure and remains keyboard coherent. | M |
| US-070-T05 | Testing | Run positive/negative role matrix tests: Test table/row/field denial, scope restriction, forged payload, publish/rollback/override denial and support access. | Automated tests prove CCSB cannot overgrant Dataverse access. | XL |
| US-070-T06 | Deployment | Package roles and access guidance: Ship roles/profiles with managed solution and document assignment, audit review, separation of duties and emergency access procedure. | Security administrator can configure roles in target environment. | M |

### US-071 — As an engineer, I want versioned validation/execute/publish/rollback Custom APIs so that all schedule mutations use a stable server contract.

**Priority / release:** P0 / V1  
**Phase:** Phase 0 — Command/API contract  
**Dependencies:** US-004, US-070  
**Primary risk:** API allows direct/unvalidated mutation  
**Traceability:** FR-API-001; NFR-SEC-003  
**Acceptance outcome:** No direct client mutation; request/response/negative tests; contracts documented.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-071-T01 | Technical | Define versioned API envelopes: Specify input/output DTOs, operation types, errors, correlation/idempotency, row versions, confirmation token, paging/refresh scope and API versioning. | OpenAPI-like contract documentation and typed client/server models are generated or maintained together. | L |
| US-071-T02 | Technical | Implement Custom API endpoints: Implement ValidateScheduleOperation, ExecuteScheduleOperation, PublishSchedule, RollbackSchedule, ValidateBoardVersion and ActivateBoardVersion with plug-in handlers. | All state changes occur through audited server commands; PCF has no direct CRUD route. | XL |
| US-071-T03 | Validation | Implement idempotency and concurrency controls: Persist/resolve idempotency key, proposal hash and row version checks; define deterministic duplicate/stale responses. | Retry cannot duplicate state change and stale write has predictable result. | L |
| US-071-T04 | Security | Harden API boundary: Authenticate via platform identity, authorise per action/scope, validate payload references against mappings and redact sensitive errors. | Penetration/code review confirms no arbitrary entity/field mutation path. | L |
| US-071-T05 | Testing | Create API contract and fault tests: Test schema, version negotiation, positive/negative operation, duplicate retry, malformed payload, token expiry, exception rollback and timing. | Automated API suite runs in CI and reports contract compatibility. | XL |
| US-071-T06 | Documentation | Publish API and extension guidance: Document supported resolver/operation extension contract, constraints, error semantics, versioning and deprecation policy. | Extension consumer can integrate without modifying scheduler core. | M |

### US-072 — As a support analyst, I want correlation across UI, operation, audit, conflict and snapshot records so that I can diagnose an outcome end to end.

**Priority / release:** P1 / V1  
**Phase:** Phase 4 — Audit/supportability  
**Dependencies:** US-071  
**Primary risk:** Insufficient traceability or sensitive telemetry  
**Traceability:** FR-AUD-001; NFR-OBS-001  
**Acceptance outcome:** Correlation query returns linked evidence without raw sensitive telemetry.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-072-T01 | Data | Define correlation and audit model: Standardize correlation ID, operation ID, UI request reference, source record reference, rule/conflict/snapshot/outbox linkage and safe diagnostic metadata. | All relevant tables carry queryable correlation fields. | M |
| US-072-T02 | Technical | Implement structured operation/audit writes: Write operation, operation items, audit, conflict/snapshot links and latency/result codes in command transaction. | End-to-end trace survives retry, warning confirmation, failure and rollback cases. | L |
| US-072-T03 | UX | Provide support diagnostics view: Create support-restricted timeline of operation outcome, correlation search, linked records and safe error details. | Support analyst can diagnose a case without browser logs or raw sensitive telemetry. | M |
| US-072-T04 | Observability | Define privacy-safe telemetry schema: Emit latency, result codes, rule outcomes and scope counts; explicitly exclude names, free text and protected details unless approved. | Telemetry/log review confirms minimisation and tenant isolation. | M |
| US-072-T05 | Testing | Run traceability exercises: Execute operation, conflict, publish and rollback then query from correlation ID in support view; verify denied support access. | Trace exercise demonstrates complete link chain and no sensitive leakage. | L |
| US-072-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

## E09 - Quality and release gates

### US-080 — As a QA lead, I want performance tests at the reference profile so that the scheduler is released with measured scale evidence.

**Priority / release:** P0 / V1  
**Phase:** Phase 5 — Release evidence  
**Dependencies:** US-031, US-042, US-060, US-061, US-062, US-072  
**Primary risk:** Unproven scale/performance threshold  
**Traceability:** NFR-PER-003..006  
**Acceptance outcome:** Initial load, slice refresh, validation and interaction targets measured at 20 concurrent users.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-080-T01 | Performance | Establish reference performance dataset: Seed representative five-level hierarchy, 100-resource page, 31-day range, 5,000 working-set assignment/overlay events, rules and publish data. | Dataset is deterministic, versioned and reusable in performance environment. | L |
| US-080-T02 | Performance | Instrument client and server timings: Capture shell render, slice refresh, DnD/keyboard responsiveness, query payload, validation and publish timings with correlation. | Metrics map directly to NFR-PER-003..006 targets. | L |
| US-080-T03 | Testing | Build automated performance suite: Create cold/warm load, date/filter change, scroll, drag preview, standard move/resize/assign validation and 20-concurrent-user scenarios. | Suite produces p50/p95 report and fails build/release gate on regression. | XL |
| US-080-T04 | Performance | Tune query, render and cache bottlenecks: Use profiling evidence to reduce payload/DOM/re-render, optimise paging/overscan and bound resolver/rule work. | Measured target improvements are documented with before/after evidence. | L |
| US-080-T05 | Deployment | Publish performance limits and monitoring thresholds: Document supported reference profile, configuration assumptions, degradation behavior and alert/triage thresholds. | Release package includes performance evidence and support runbook. | M |

### US-081 — As an accessibility specialist, I want task-based keyboard and assistive-technology validation so that all core scheduling functions are usable without drag/drop.

**Priority / release:** P0 / V1  
**Phase:** Phase 5 — Release evidence  
**Dependencies:** US-030, US-031, US-040, US-041, US-042, US-060, US-062  
**Primary risk:** Pointer-only or inaccessible custom timeline controls  
**Traceability:** NFR-UX-001/002  
**Acceptance outcome:** Focused tests cover selection, forms, commands, errors, publish and rollback.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-081-T01 | UX | Create accessibility interaction specification: Define focus order, row/timeline navigation, selection, keyboard DnD semantics, form alternatives, live regions, labels and contrast requirements. | Specification covers every core scheduling action and responsive panel behavior. | L |
| US-081-T02 | Technical | Implement semantic/focus foundations: Use Fluent UI accessible primitives; add ARIA roles/names, visible focus, roving focus strategy, keyboard shortcuts and live announcements. | No custom timeline action requires pointer-only interaction. | XL |
| US-081-T03 | UX | Provide non-colour status representation: Add text/icon/pattern equivalents for status, warning, lock, overlay and requirement indicators. | Visual QA proves meaningful state under monochrome/contrast constraints. | M |
| US-081-T04 | Testing | Run automated accessibility checks: Integrate linting/axe-like checks for custom UI and test keyboard sequence on primary workflows. | Automated checks block known critical violations. | L |
| US-081-T05 | Testing | Run manual assistive-technology scenarios: Validate screen reader and keyboard flows for selection, create/edit, assign, move/resize form, warning, publish, rollback and error states. | WCAG 2.2 AA intent evidence and defects are documented/resolved or accepted formally. | XL |
| US-081-T06 | Deployment | Register solution component and release evidence: Add this capability's solution assets, feature/configuration migration considerations, traceability links and operational notes to the release package. | Managed deployment contains the required assets and release evidence identifies compatibility, rollback and support implications. | S |

### US-082 — As a release manager, I want an upgrade rehearsal and support runbook so that configuration and operational issues are recoverable.

**Priority / release:** P1 / V1  
**Phase:** Phase 5 — Release evidence  
**Dependencies:** US-001, US-002, US-013, US-061, US-062, US-080, US-081  
**Primary risk:** Upgrade/support recovery is untested  
**Traceability:** NFR-ALM-002/003; NFR-SUP-001  
**Acceptance outcome:** Managed import/compatibility/rollback rehearsed; support workflows signed off.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-082-T01 | Deployment | Define release/upgrade rehearsal plan: Document source/target versions, managed solution import, configuration compatibility, projection regeneration, role/environment setup, rollback and success criteria. | Plan covers clean install and upgrade from all supported versions. | M |
| US-082-T02 | Testing | Execute upgrade and rollback rehearsals: Run automated/manual rehearsal in clean and upgrade-like environments with active configuration, snapshots and locks. | Evidence shows no schema/config corruption and clear recovery path for intentional failure. | XL |
| US-082-T03 | Documentation | Create operational support runbook: Document configuration failure, stale write, failed publish/rollback, lock issue, mapping issue, performance triage, escalation, retention and evidence collection. | Runbook passes tabletop support scenario with named roles and SLAs. | L |
| US-082-T04 | Observability | Set release gates and health checks: Define go/no-go checklist for security, performance, accessibility, API contract, installation, support, monitoring and known limitations. | Release candidate cannot progress without recorded evidence/approvals. | M |
| US-082-T05 | Deployment | Produce release notes and customer guidance: Document version changes, compatibility/migration impacts, limitations, upgrade steps and support contact responsibilities. | Customer-facing and internal notes are reviewed and versioned. | M |

## E10 - Deferred direction

### US-090 — As a scheduler, I want split/merge operations so that work can be decomposed or combined with governed graph semantics.

**Priority / release:** Later / Later  
**Phase:** Deferred — Design gate  
**Dependencies:** US-062, US-082  
**Primary risk:** Graph/publish semantics unsupported  
**Traceability:** FR-LTR-001  
**Acceptance outcome:** Not V1. Requires design approval for event graph, audit, publish and rollback semantics.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-090-T01 | Discovery | Retain as deferred V1 item: Mark split/merge as excluded from V1; prohibit scope creep through feature flags or UI stubs that imply support. | V1 release documentation and acceptance suite explicitly exclude split/merge. | S |
| US-090-T02 | Architecture | Create future graph-mutation design gate: Before prioritisation, define split/merge identity, parent/child relationship, requirement/allocation, audit, publish/rollback and conflict semantics. | Architecture decision record approved before any implementation estimate. | M |
| US-090-T03 | Testing | Define future regression charter: Specify data migration, atomicity, concurrency, snapshot/rollback and accessibility scenarios required for a future release. | Test charter is attached to deferred story; no V1 test dependency. | S |

### US-091 — As a mobile user, I want offline scheduling so that I can work without connectivity.

**Priority / release:** Later / Later  
**Phase:** Deferred — Design gate  
**Dependencies:** US-082  
**Primary risk:** Offline sync and conflict data loss  
**Traceability:** FR-LTR-001; NFR-UX-005  
**Acceptance outcome:** Not V1. Requires mobile/offline profile, synchronization, conflict policy and dedicated NFR baseline.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-091-T01 | Discovery | Retain offline/mobile as deferred V1 item: Do not claim mobile/offline capability in V1 positioning, demos or acceptance tests. | Scope and release notes explicitly exclude mobile/offline scheduling. | S |
| US-091-T02 | Architecture | Create mobile/offline feasibility design: Define offline profile, supported tables, local cache/encryption, sync batching, conflict rules, payload sizing, device security and accessibility. | Separate architecture/NFR baseline and threat model approved before build. | L |
| US-091-T03 | Testing | Define field-sync test charter: Plan connectivity loss, merge conflict, partial sync, device loss, performance and browser/device accessibility tests. | Future tests are scoped and acceptance conditions are measurable. | M |

### US-092 — As an integration owner, I want outbound connectors so that schedule changes can inform other platforms.

**Priority / release:** Later / Later  
**Phase:** Deferred — Design gate  
**Dependencies:** US-071, US-072, US-082  
**Primary risk:** Connector failures affect transaction integrity  
**Traceability:** FR-LTR-001  
**Acceptance outcome:** Not V1. Requires outbox delivery, retries, idempotency, security and monitoring design.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-092-T01 | Discovery | Retain connectors as deferred V1 item: Keep all external calls outside V1 schedule transactions and avoid unapproved direct webhook calls. | V1 architecture/security review confirms no connector delivery in transaction path. | S |
| US-092-T02 | Architecture | Define outbox and delivery contract: Specify event schema, tenant isolation, delivery worker, retries/backoff, idempotency, DLQ, secret management, monitoring and replay policy. | ADR, threat model and operational ownership approved before implementation. | L |
| US-092-T03 | Testing | Define connector reliability suite: Plan delayed/duplicate/failing receiver, replay, webhook signature, privacy, rate limit and committed-transaction integrity tests. | Future test charter assures connector failure cannot reverse schedule state. | M |

### US-093 — As an enterprise user, I want URS/Field Service/Project Operations adapters so that selected data can interoperate.

**Priority / release:** Later / Later  
**Phase:** Deferred — Design gate  
**Dependencies:** US-011, US-071, US-082  
**Primary risk:** Licensing/model drift makes adapter unmaintainable  
**Traceability:** Scope  
**Acceptance outcome:** Not V1. Requires licensed contract, regression and support matrix.

| Task ID | Category | Task | Definition of done | Est. |
|---|---|---|---|---|
| US-093-T01 | Discovery | Retain adapters as deferred V1 item: Do not position CCSB as URS/Field Service/Project Operations replacement or adapter in V1. | Market material and release notes state exclusion clearly. | S |
| US-093-T02 | Architecture | Assess licensed adapter contracts: Evaluate target entity model, licensing, security, ownership, sync direction, conflict authority, versioning and support/regression cost. | Commercial and technical feasibility decision is recorded before build. | L |
| US-093-T03 | Testing | Define interoperability regression charter: Plan mapping, reconciliation, upgrade, throttling, Dataverse security and failure recovery tests for any selected adapter. | Future test scope and support matrix are approved. | M |

## Deferred backlog rules

US-090 to US-093 must remain out of V1 build, performance, accessibility and release-acceptance scope. They are intentionally retained only as architecture/test design gates. They may enter a later release only after a separate scope decision, NFR/threat review, data-contract design, commercial justification and regression charter.

## Backlog import use

The accompanying CSV files are parent-keyed for import into tools such as Azure DevOps or Jira. Import epics first, then user stories with `EpicID`, then tasks with `ParentStoryID`. Preserve IDs as immutable external references; use the tool's own generated identifier as its internal work-item ID.

## Source basis

- CCSB Consolidated Project Document v2.1 — PCF Controls Added, controlled baseline, 4 July 2026.
- CCSB Deep Market Research, Competitive Analysis & Long-Term Viability, 21 June 2026.