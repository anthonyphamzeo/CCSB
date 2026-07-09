# Planora First Release Implementation Order v1.0

Generated from:

- `Black_Logs/Personal_Plan_V1/Planora_Personal_MVP_Scope_Advice_v1_0.md`
- `Black_Logs/CCSB_Backlog_v1_1_PCF_Controls_Package_HTML/CCSB_Backlog_Import_User_Stories_v1_1.csv`
- `Black_Logs/CCSB_Backlog_v1_1_PCF_Controls_Package_HTML/CCSB_Backlog_Import_Tasks_v1_1.csv`

## Release interpretation

Release 1 is the personal/native MVP from the plan, not the full enterprise V1 backlog. The implementation should prove one native CCSB board, the Runtime PCF, multi-resource assignment, controlled server-side operations, basic validation, targeted refresh and minimal audit evidence.

The updated backlog adds the Configuration Studio PCF (`US-014`). For Release 1, implement `US-014-T01` and `US-014-T02` only so the boundary, information architecture and deployable PCF shell exist. Complete `US-014-T03` through `US-014-T11` after the runtime board and operation contracts have proven the configuration shape.

## ALM sequencing rules

- Keep schema, Custom APIs, plug-ins, PCFs, security roles and configuration assets in the solution/repository from the start.
- Export or back up the unmanaged development solution before schema changes while only one environment exists.
- Preserve the no-direct-write rule: PCFs read governed slices and mutate only through versioned Custom APIs.
- Use one work item branch per task and keep schema, API and PCF concerns reviewable.
- Treat model-driven forms and seeded native configuration as the Release 1 authoring path; the Configuration Studio becomes productisation work after the runtime proof.
- Start accessibility and instrumentation early, but reserve formal 20-user performance, full upgrade rehearsal and formal assistive-technology evidence for commercial hardening.

## Prioritized tasks to implement first

### 01. Establish the ALM skeleton before schema work

Start with a source-controlled solution, dependency manifest, environment settings and import guardrails.

001. `US-001-T01` - Create managed-solution baseline (Deployment; size L; story US-001)
002. `US-001-T02` - Define component dependency manifest (Technical; size M; story US-001)
003. `US-001-T03` - Provision environment configuration (Data; size M; story US-001)
004. `US-001-T05` - Implement preflight import checks (Validation; size M; story US-001)

### 02. Lock the native data foundation

Implement the physical ccsb_* model, native schedule graph, ownership, keys, query shapes and deterministic test data.

005. `US-004-T01` - Produce physical schema specification (Data; size L; story US-004)
006. `US-004-T02` - Implement product-owned configuration tables (Data; size L; story US-004)
007. `US-004-T03` - Implement control, audit and publish tables (Data; size L; story US-004)
008. `US-004-T04` - Implement optional native schedule graph (Data; size L; story US-004)
009. `US-004-T05` - Define keys, relationships and lifecycle values (Data; size M; story US-004)
010. `US-004-T06` - Define ownership and access model (Security; size M; story US-004)
011. `US-004-T07` - Review query and indexing shapes (Performance; size M; story US-004)
012. `US-004-T08` - Create schema validation and compatibility checks (Validation; size L; story US-004)
013. `US-004-T09` - Build data factory and integrity test suite (Testing; size L; story US-004)
014. `US-004-T10` - Deliver schema migration and upgrade policy (Deployment; size L; story US-004)

### 03. Add the minimum compatibility, security and command boundary

The PCFs must not become direct writers, so compatibility metadata, authorisation and versioned APIs come before UI operations.

015. `US-002-T01` - Define product and schema compatibility contract (Technical; size M; story US-002)
016. `US-002-T02` - Add compatibility metadata (Data; size M; story US-002)
017. `US-002-T03` - Implement pre-activation compatibility validation (Validation; size L; story US-002)
018. `US-070-T01` - Define permission model and matrix (Security; size L; story US-070)
019. `US-070-T02` - Implement permission profiles and assignments (Data; size M; story US-070)
020. `US-070-T03` - Build server-side authorisation service (Technical; size L; story US-070)
021. `US-070-T05` - Run positive/negative role matrix tests (Testing; size XL; story US-070)
022. `US-071-T01` - Define versioned API envelopes (Technical; size L; story US-071)
023. `US-071-T02` - Implement Custom API endpoints (Technical; size XL; story US-071)
024. `US-071-T03` - Implement idempotency and concurrency controls (Validation; size L; story US-071)
025. `US-071-T04` - Harden API boundary (Security; size L; story US-071)
026. `US-071-T05` - Create API contract and fault tests (Testing; size XL; story US-071)
027. `US-071-T06` - Publish API and extension guidance (Documentation; size M; story US-071)

### 04. Create one governed board configuration and projection

Use model-driven forms and seeded/native configuration first; do not build generic customer mapping ahead of the runtime proof.

028. `US-003-T01` - Model board registry and tenant isolation (Data; size M; story US-003)
029. `US-003-T02` - Implement board resolution service (Technical; size M; story US-003)
030. `US-003-T04` - Enforce single active board version (Validation; size M; story US-003)
031. `US-010-T01` - Implement board-version aggregate (Data; size L; story US-010)
032. `US-010-T02` - Implement create, clone, edit and compare flows (Functional; size L; story US-010)
033. `US-010-T03` - Design version-management administration (UX; size M; story US-010)
034. `US-010-T04` - Protect immutability and lifecycle transitions (Validation; size M; story US-010)
035. `US-010-T05` - Test clone, compare and concurrent-edit cases (Testing; size L; story US-010)
036. `US-010-T06` - Add version lifecycle migration and documentation (Deployment; size M; story US-010)
037. `US-022-T01` - Implement roles and requirements model (Data; size L; story US-022)
038. `US-022-T02` - Build role and requirement configuration (Functional; size L; story US-022)
039. `US-022-T03` - Design requirement editing and summary (UX; size M; story US-022)
040. `US-022-T04` - Create eligibility and allocation calculator (Technical; size L; story US-022)
041. `US-022-T05` - Enforce role and capacity policy (Validation; size L; story US-022)
042. `US-022-T06` - Test multi-resource and capacity scenarios (Testing; size L; story US-022)
043. `US-022-T07` - Register solution component and release evidence (Deployment; size S; story US-022)
044. `US-013-T01` - Define runtime projection schema (Technical; size M; story US-013)
045. `US-013-T02` - Implement projection generator (Technical; size L; story US-013)
046. `US-013-T03` - Detect stale or incompatible projections (Validation; size M; story US-013)
047. `US-013-T04` - Expose projection health (UX; size M; story US-013)
048. `US-013-T05` - Test projection integrity and cache keys (Testing; size L; story US-013)
049. `US-013-T06` - Package projection regeneration on import/upgrade (Deployment; size M; story US-013)

### 05. Account for the new Configuration Studio PCF without letting it lead the release

Do the boundary and deployable shell now; defer the full authoring workbench until runtime contracts have survived the MVP.

050. `US-014-T01` - Define Configuration Studio PCF boundary and interaction specification (Functional; size M; story US-014)
051. `US-014-T02` - Create Planora Configuration Studio PCF solution and host shell (Technical; size L; story US-014)

### 06. Build the Runtime PCF and read-only board workspace

This is the visible product proof: active projection bootstrap, board/date context, rows and weekly timeline.

052. `US-029-T01` - Define Runtime PCF and Projection Controller boundary (Technical; size M; story US-029)
053. `US-029-T02` - Create Planora Schedule Board Runtime PCF and model-driven host shell (Technical; size L; story US-029)
054. `US-029-T03` - Implement active board projection bootstrap and fail-closed controller (Technical; size L; story US-029)
055. `US-029-T04` - Implement visible-slice read client, cache and obsolete-request cancellation (Technical; size XL; story US-029)
056. `US-029-T05` - Build runtime state composition and region integration contract (Technical; size L; story US-029)
057. `US-029-T06` - Implement governed command adapter and proposal state handling (Functional; size XL; story US-029)
058. `US-029-T07` - Implement targeted refresh and result reconciliation controller (Technical; size L; story US-029)
059. `US-029-T08` - Add runtime security, telemetry and support-safe diagnostics (Security; size L; story US-029)
060. `US-029-T09` - Complete Runtime PCF contract, integration, performance and accessibility tests (Testing; size XL; story US-029)
061. `US-029-T10` - Package Runtime PCF, host integration and operational support guidance (Deployment; size M; story US-029)
062. `US-030-T01` - Implement board-context bootstrap (Technical; size L; story US-030)
063. `US-030-T02` - Build workspace command bar (UX; size L; story US-030)
064. `US-030-T03` - Implement timezone-safe navigation (Functional; size M; story US-030)
065. `US-030-T04` - Apply permitted-board filtering (Security; size M; story US-030)
066. `US-030-T05` - Fail closed on invalid board/version (Validation; size M; story US-030)
067. `US-030-T06` - Test context and timezone matrix (Testing; size L; story US-030)
068. `US-030-T07` - Register solution component and release evidence (Deployment; size S; story US-030)
069. `US-031-T01` - Implement read-model query contracts (Technical; size L; story US-031)
070. `US-031-T02` - Build virtualised scheduler engine shell (Technical; size XL; story US-031)
071. `US-031-T03` - Implement visible-slice cache and cancellation (Technical; size L; story US-031)
072. `US-031-T04` - Design progressive load and empty/error states (UX; size M; story US-031)
073. `US-031-T05` - Set performance budgets and instrumentation (Performance; size L; story US-031)
074. `US-031-T06` - Run viewport/paging/performance tests (Testing; size XL; story US-031)
075. `US-031-T07` - Register solution component and release evidence (Deployment; size S; story US-031)

### 07. Implement controlled schedule operations

Create/edit, assign, explain validation, then move/reassign through validate -> execute -> audit -> targeted refresh.

076. `US-040-T01` - Define create/edit operation semantics (Functional; size L; story US-040)
077. `US-040-T02` - Build accessible booking/activity forms (UX; size L; story US-040)
078. `US-040-T03` - Implement validate/execute handling (Technical; size L; story US-040)
079. `US-040-T04` - Map defaults and managed fields (Data; size M; story US-040)
080. `US-040-T05` - Enforce interval and parent rules (Validation; size L; story US-040)
081. `US-040-T06` - Test create/edit paths (Testing; size L; story US-040)
082. `US-040-T07` - Register solution component and release evidence (Deployment; size S; story US-040)
083. `US-041-T01` - Define assign/unassign/reassign semantics (Functional; size L; story US-041)
084. `US-041-T02` - Build assignment controls (UX; size L; story US-041)
085. `US-041-T03` - Implement assignment command handlers (Technical; size L; story US-041)
086. `US-041-T04` - Resolve resource, role and activity mapping (Data; size M; story US-041)
087. `US-041-T05` - Validate eligibility and capacity (Validation; size L; story US-041)
088. `US-041-T06` - Test group-work cases (Testing; size L; story US-041)
089. `US-041-T07` - Register solution component and release evidence (Deployment; size S; story US-041)
090. `US-051-T01` - Define rule outcome contract (Data; size M; story US-051)
091. `US-051-T02` - Implement rule pipeline (Technical; size XL; story US-051)
092. `US-051-T03` - Build conflict and confirmation dialog (UX; size L; story US-051)
093. `US-051-T04` - Secure confirmation tokens (Validation; size L; story US-051)
094. `US-051-T05` - Test pass/warn/block behavior (Testing; size L; story US-051)
095. `US-051-T06` - Capture rule diagnostics (Observability; size M; story US-051)
096. `US-051-T07` - Register solution component and release evidence (Deployment; size S; story US-051)
097. `US-042-T01` - Define move/resize/reassign delta rules (Functional; size L; story US-042)
098. `US-042-T02` - Implement drag, resize and form alternatives (UX; size XL; story US-042)
099. `US-042-T03` - Implement validate-confirm-execute orchestration (Technical; size L; story US-042)
100. `US-042-T04` - Evaluate affected graph and locks (Validation; size XL; story US-042)
101. `US-042-T05` - Test mutation, warning and stale paths (Testing; size XL; story US-042)
102. `US-042-T06` - Record operation evidence (Observability; size M; story US-042)
103. `US-042-T07` - Register solution component and release evidence (Deployment; size S; story US-042)
104. `US-050-T01` - Define completion and allocation measures (Data; size M; story US-050)
105. `US-050-T02` - Implement shared requirement calculator (Technical; size L; story US-050)
106. `US-050-T03` - Render accessible allocation indicators (UX; size M; story US-050)
107. `US-050-T04` - Apply coverage rules (Validation; size M; story US-050)
108. `US-050-T05` - Test calculation matrix (Testing; size L; story US-050)
109. `US-050-T06` - Register solution component and release evidence (Deployment; size S; story US-050)

### 08. Add release-demo evidence and accessibility foundations

Record basic operation evidence, instrument the client/server path and keep keyboard/accessibility foundations in the first build.

110. `US-072-T01` - Define correlation and audit model (Data; size M; story US-072)
111. `US-072-T02` - Implement structured operation/audit writes (Technical; size L; story US-072)
112. `US-072-T04` - Define privacy-safe telemetry schema (Observability; size M; story US-072)
113. `US-080-T02` - Instrument client and server timings (Performance; size L; story US-080)
114. `US-081-T01` - Create accessibility interaction specification (UX; size L; story US-081)
115. `US-081-T02` - Implement semantic/focus foundations (Technical; size XL; story US-081)
116. `US-081-T03` - Provide non-colour status representation (UX; size M; story US-081)
117. `US-081-T04` - Run automated accessibility checks (Testing; size L; story US-081)
118. `US-001-T04` - Provide install verification surface (UX; size S; story US-001)
119. `US-001-T07` - Publish installation and rollback runbook (Documentation; size M; story US-001)

## Full ordered sequence of user stories and tasks

Use this as the end-to-end dependency order. Tasks are listed once in their recommended implementation position; the checkbox state is intentionally blank for tracking.

## Foundation ALM and clean install baseline

### US-001 - Phase 0 - ALM & solution scaffold - P0 / V1

Story: As a solution administrator, I want to install CCSB as a managed solution with required roles and environment settings so that the product is governed through standard ALM.  
Dependencies: None  
Acceptance outcome: Import validates required components; roles are installed; version is visible; unsupported dependencies fail clearly.

- [ ] `US-001-T01` - Create managed-solution baseline (Deployment; size L; depends: None)
- [ ] `US-001-T02` - Define component dependency manifest (Technical; size M; depends: None)
- [ ] `US-001-T03` - Provision environment configuration (Data; size M; depends: None)
- [ ] `US-001-T04` - Provide install verification surface (UX; size S; depends: None)
- [ ] `US-001-T05` - Implement preflight import checks (Validation; size M; depends: None)
- [ ] `US-001-T06` - Automate clean-environment install tests (Testing; size L; depends: None)
- [ ] `US-001-T07` - Publish installation and rollback runbook (Documentation; size M; depends: None)

## Physical data model and native graph

### US-004 - Phase 0 - Data foundation - P0 / V1

Story: As a solution architect, I want CCSB's physical Dataverse data model, keys, relationships, ownership, lifecycle and retention controls implemented so that the product has a supportable, upgrade-safe data foundation.  
Dependencies: US-001  
Acceptance outcome: The managed solution contains documented ccsb_* tables, relationships, keys, choice/status lifecycles, security/ownership design, migration/seed strategy and validation for the optional native schedule graph.

- [ ] `US-004-T01` - Produce physical schema specification (Data; size L; depends: US-001)
- [ ] `US-004-T02` - Implement product-owned configuration tables (Data; size L; depends: US-001)
- [ ] `US-004-T03` - Implement control, audit and publish tables (Data; size L; depends: US-001)
- [ ] `US-004-T04` - Implement optional native schedule graph (Data; size L; depends: US-001)
- [ ] `US-004-T05` - Define keys, relationships and lifecycle values (Data; size M; depends: US-001)
- [ ] `US-004-T06` - Define ownership and access model (Security; size M; depends: US-001)
- [ ] `US-004-T07` - Review query and indexing shapes (Performance; size M; depends: US-001)
- [ ] `US-004-T08` - Create schema validation and compatibility checks (Validation; size L; depends: US-001)
- [ ] `US-004-T09` - Build data factory and integrity test suite (Testing; size L; depends: US-001)
- [ ] `US-004-T10` - Deliver schema migration and upgrade policy (Deployment; size L; depends: US-001)

## Compatibility contract

### US-002 - Phase 0 - Compatibility contract - P0 / V1

Story: As a release manager, I want configuration schema and product compatibility checks so that incompatible configurations do not activate after an upgrade.  
Dependencies: US-004  
Acceptance outcome: Validation detects incompatible schema; activation is blocked; diagnostics identify migration action.

- [ ] `US-002-T01` - Define product and schema compatibility contract (Technical; size M; depends: US-004)
- [ ] `US-002-T02` - Add compatibility metadata (Data; size M; depends: US-004)
- [ ] `US-002-T03` - Implement pre-activation compatibility validation (Validation; size L; depends: US-004)
- [ ] `US-002-T04` - Design administrator diagnostics (UX; size M; depends: US-004)
- [ ] `US-002-T05` - Test upgrade and downgrade boundaries (Testing; size L; depends: US-004)
- [ ] `US-002-T06` - Package migration scripts and release notes (Deployment; size M; depends: US-004)

## Security foundation

### US-070 - Phase 0 - Security foundation - P0 / V1

Story: As a security administrator, I want CCSB action permissions layered below Dataverse access so that the product does not overgrant customer data.  
Dependencies: US-004  
Acceptance outcome: Permission cannot bypass Dataverse security; negative role tests pass.

- [ ] `US-070-T01` - Define permission model and matrix (Security; size L; depends: US-004)
- [ ] `US-070-T02` - Implement permission profiles and assignments (Data; size M; depends: US-004)
- [ ] `US-070-T03` - Build server-side authorisation service (Technical; size L; depends: US-004)
- [ ] `US-070-T04` - Design permission-aware actions (UX; size M; depends: US-004)
- [ ] `US-070-T05` - Run positive/negative role matrix tests (Testing; size XL; depends: US-004)
- [ ] `US-070-T06` - Package roles and access guidance (Deployment; size M; depends: US-004)

## Versioned Custom API boundary

### US-071 - Phase 0 - Command/API contract - P0 / V1

Story: As an engineer, I want versioned validation/execute/publish/rollback Custom APIs so that all schedule mutations use a stable server contract.  
Dependencies: US-004, US-070  
Acceptance outcome: No direct client mutation; request/response/negative tests; contracts documented.

- [ ] `US-071-T01` - Define versioned API envelopes (Technical; size L; depends: US-004, US-070)
- [ ] `US-071-T02` - Implement Custom API endpoints (Technical; size XL; depends: US-004, US-070)
- [ ] `US-071-T03` - Implement idempotency and concurrency controls (Validation; size L; depends: US-004, US-070)
- [ ] `US-071-T04` - Harden API boundary (Security; size L; depends: US-004, US-070)
- [ ] `US-071-T05` - Create API contract and fault tests (Testing; size XL; depends: US-004, US-070)
- [ ] `US-071-T06` - Publish API and extension guidance (Documentation; size M; depends: US-004, US-070)

## Environment board boundary

### US-003 - Phase 0 - Tenant/board boundary - P1 / V1

Story: As a product owner, I want an environment-level board registry so that each Dataverse environment is an isolated CCSB tenant.  
Dependencies: US-004, US-070  
Acceptance outcome: Board keys unique per environment; no cross-environment lookup/administration path exists.

- [ ] `US-003-T01` - Model board registry and tenant isolation (Data; size M; depends: US-004, US-070)
- [ ] `US-003-T02` - Implement board resolution service (Technical; size M; depends: US-004, US-070)
- [ ] `US-003-T03` - Build board selection and empty-state flow (UX; size M; depends: US-004, US-070)
- [ ] `US-003-T04` - Enforce single active board version (Validation; size M; depends: US-004, US-070)
- [ ] `US-003-T05` - Run isolation and authorisation tests (Testing; size M; depends: US-004, US-070)
- [ ] `US-003-T06` - Seed sample registry records (Deployment; size S; depends: US-004, US-070)

## Board version lifecycle

### US-010 - Phase 1 - Configuration foundation - P0 / V1

Story: As a board administrator, I want to create and clone board versions so that configuration changes do not alter an active board unexpectedly.  
Dependencies: US-004, US-002  
Acceptance outcome: Active version cannot be edited; clone begins as Draft; compare shows changes.

- [ ] `US-010-T01` - Implement board-version aggregate (Data; size L; depends: US-004, US-002)
- [ ] `US-010-T02` - Implement create, clone, edit and compare flows (Functional; size L; depends: US-004, US-002)
- [ ] `US-010-T03` - Design version-management administration (UX; size M; depends: US-004, US-002)
- [ ] `US-010-T04` - Protect immutability and lifecycle transitions (Validation; size M; depends: US-004, US-002)
- [ ] `US-010-T05` - Test clone, compare and concurrent-edit cases (Testing; size L; depends: US-004, US-002)
- [ ] `US-010-T06` - Add version lifecycle migration and documentation (Deployment; size M; depends: US-004, US-002)

## Mapped entity configuration - productise after native MVP

### US-011 - Phase 1 - Configuration foundation - P0 / V1

Story: As a board administrator, I want to map Booking, Activity, Assignment and Resource entities so that CCSB can use customer-owned Dataverse data.  
Dependencies: US-004, US-010  
Acceptance outcome: Metadata selectors validate tables/relationships; missing mandatory mapping blocks activation.

- [ ] `US-011-T01` - Define mapping semantic catalogue (Data; size L; depends: US-004, US-010)
- [ ] `US-011-T02` - Build Dataverse metadata discovery service (Technical; size L; depends: US-004, US-010)
- [ ] `US-011-T03` - Build mapping administration wizard (UX; size L; depends: US-004, US-010)
- [ ] `US-011-T04` - Validate graph cardinality and field types (Validation; size L; depends: US-004, US-010)
- [ ] `US-011-T05` - Create typed runtime mapping resolver (Technical; size L; depends: US-004, US-010)
- [ ] `US-011-T06` - Test mapped and native graph modes (Testing; size L; depends: US-004, US-010)
- [ ] `US-011-T07` - Publish supported mapping patterns (Documentation; size M; depends: US-004, US-010)

## Write and rollback policy - productise after native MVP

### US-012 - Phase 1 - Configuration foundation - P0 / V1

Story: As a board administrator, I want to map write and rollback-managed fields separately so that CCSB changes only approved scheduling data.  
Dependencies: US-011  
Acceptance outcome: Write and rollback flags independently stored; rollback cannot affect unmapped/unmanaged fields.

- [ ] `US-012-T01` - Add write and rollback flags to field mappings (Data; size M; depends: US-011)
- [ ] `US-012-T02` - Create managed-field policy editor (Functional; size M; depends: US-011)
- [ ] `US-012-T03` - Validate field policy safety (Validation; size M; depends: US-011)
- [ ] `US-012-T04` - Enforce policy in command and rollback services (Technical; size L; depends: US-011)
- [ ] `US-012-T05` - Test write/rollback boundary (Testing; size L; depends: US-011)
- [ ] `US-012-T06` - Document field-governance and change procedure (Documentation; size S; depends: US-011)

## Grouping and stable path configuration

### US-020 - Phase 1 - Grouping/capacity foundation - P0 / V1

Story: As a board administrator, I want to define one to five resource grouping levels so that dispatchers can view the operating hierarchy.  
Dependencies: US-004, US-011  
Acceptance outcome: Direct field, lookup path and governed resolver options; levels are ordered; fallback label supported.

- [ ] `US-020-T01` - Implement group-definition schema (Data; size M; depends: US-004, US-011)
- [ ] `US-020-T02` - Implement grouping configuration behavior (Functional; size L; depends: US-004, US-011)
- [ ] `US-020-T03` - Build grouping editor and preview (UX; size L; depends: US-004, US-011)
- [ ] `US-020-T04` - Validate resolver safety and hierarchy limits (Validation; size L; depends: US-004, US-011)
- [ ] `US-020-T05` - Create group-path query/resolver contract (Technical; size L; depends: US-004, US-011)
- [ ] `US-020-T06` - Test grouping variants and null/fallback cases (Testing; size L; depends: US-004, US-011)
- [ ] `US-020-T07` - Register solution component and release evidence (Deployment; size S; depends: US-004, US-011)

### US-021 - Phase 1 - Grouping/capacity foundation - P1 / V1

Story: As a board administrator, I want each resource to resolve to one stable group path so that events and capacity do not duplicate across branches.  
Dependencies: US-020  
Acceptance outcome: Validation detects ambiguous/multiple paths; runtime shows a single path per board version.

- [ ] `US-021-T01` - Define stable group-path resolution algorithm (Technical; size M; depends: US-020)
- [ ] `US-021-T02` - Detect ambiguity and multi-path output (Validation; size M; depends: US-020)
- [ ] `US-021-T03` - Persist/cache path identity safely (Data; size M; depends: US-020)
- [ ] `US-021-T04` - Surface path diagnostics (UX; size S; depends: US-020)
- [ ] `US-021-T05` - Test determinism and non-duplication (Testing; size M; depends: US-020)
- [ ] `US-021-T06` - Register solution component and release evidence (Deployment; size S; depends: US-020)

## Roles and requirements

### US-022 - Phase 1 - Grouping/capacity foundation - P0 / V1

Story: As a board administrator, I want named resource roles and requirements so that group bookings can demand the right people, vehicles, rooms or equipment.  
Dependencies: US-004, US-011  
Acceptance outcome: Roles can restrict type/capability; requirement stores quantity/capacity; validation supports partial fill.

- [ ] `US-022-T01` - Implement roles and requirements model (Data; size L; depends: US-004, US-011)
- [ ] `US-022-T02` - Build role and requirement configuration (Functional; size L; depends: US-004, US-011)
- [ ] `US-022-T03` - Design requirement editing and summary (UX; size M; depends: US-004, US-011)
- [ ] `US-022-T04` - Create eligibility and allocation calculator (Technical; size L; depends: US-004, US-011)
- [ ] `US-022-T05` - Enforce role and capacity policy (Validation; size L; depends: US-004, US-011)
- [ ] `US-022-T06` - Test multi-resource and capacity scenarios (Testing; size L; depends: US-004, US-011)
- [ ] `US-022-T07` - Register solution component and release evidence (Deployment; size S; depends: US-004, US-011)

## Runtime projection

### US-013 - Phase 1 - Configuration foundation - P1 / V1

Story: As a board administrator, I want generated read-only runtime projection JSON so that runtime loading is efficient without creating a second editable configuration source.  
Dependencies: US-010, US-011, US-012, US-002  
Acceptance outcome: Projection source hash/version created after validation; manual JSON edit is not offered; stale projection blocks runtime.

- [ ] `US-013-T01` - Define runtime projection schema (Technical; size M; depends: US-010, US-011, US-012, US-002)
- [ ] `US-013-T02` - Implement projection generator (Technical; size L; depends: US-010, US-011, US-012, US-002)
- [ ] `US-013-T03` - Detect stale or incompatible projections (Validation; size M; depends: US-010, US-011, US-012, US-002)
- [ ] `US-013-T04` - Expose projection health (UX; size M; depends: US-010, US-011, US-012, US-002)
- [ ] `US-013-T05` - Test projection integrity and cache keys (Testing; size L; depends: US-010, US-011, US-012, US-002)
- [ ] `US-013-T06` - Package projection regeneration on import/upgrade (Deployment; size M; depends: US-010, US-011, US-012, US-002)

## Configuration Studio PCF early boundary and shell

### US-014 - Phase 1 - Configuration experience - P0 / V1

Story: As a Configuration Administrator, I want a guided Planora Configuration Studio PCF so that I can create, edit, validate, preview, version and activate Schedule Board configurations without manually maintaining interdependent ccsb_* records.  
Dependencies: US-010, US-011, US-012, US-013, US-020, US-021, US-022, US-070, US-071  
Acceptance outcome: A Configuration Administrator can author draft versions through metadata-aware screens; active versions remain immutable; configuration validation, projection generation and activation use governed APIs; model-driven forms remain the support and low-level administration fallback.

- [ ] `US-014-T01` - Define Configuration Studio PCF boundary and interaction specification (Functional; size M; depends: US-010, US-011, US-012, US-013)
- [ ] `US-014-T02` - Create Planora Configuration Studio PCF solution and host shell (Technical; size L; depends: US-001, US-010, US-070)

## Runtime PCF and projection controller

### US-029 - Phase 2 - Runtime PCF foundation - P0 / V1

Story: As a scheduler, I want the Planora Schedule Board Runtime PCF and Projection Controller to resolve an active, validated board projection, compose the operational workspace and route all actions through governed APIs so that the board is fast, safe and consistent.  
Dependencies: US-001, US-003, US-013, US-070, US-071  
Acceptance outcome: The Runtime PCF loads only active validated compatible projections, fails closed for missing/stale/incompatible projection, performs visible-slice reads, routes all mutations through Custom APIs, refreshes only affected scope and does not directly write schedule, configuration or control records.

- [ ] `US-029-T01` - Define Runtime PCF and Projection Controller boundary (Technical; size M; depends: US-013, US-070, US-071)
- [ ] `US-029-T02` - Create Planora Schedule Board Runtime PCF and model-driven host shell (Technical; size L; depends: US-001, US-003, US-070)
- [ ] `US-029-T03` - Implement active board projection bootstrap and fail-closed controller (Technical; size L; depends: US-003, US-013, US-070, US-071)
- [ ] `US-029-T04` - Implement visible-slice read client, cache and obsolete-request cancellation (Technical; size XL; depends: US-013, US-070)
- [ ] `US-029-T05` - Build runtime state composition and region integration contract (Technical; size L; depends: US-001, US-003, US-013, US-070)
- [ ] `US-029-T06` - Implement governed command adapter and proposal state handling (Functional; size XL; depends: US-071, US-070)
- [ ] `US-029-T07` - Implement targeted refresh and result reconciliation controller (Technical; size L; depends: US-013, US-071)
- [ ] `US-029-T08` - Add runtime security, telemetry and support-safe diagnostics (Security; size L; depends: US-070, US-071)
- [ ] `US-029-T09` - Complete Runtime PCF contract, integration, performance and accessibility tests (Testing; size XL; depends: US-001, US-003, US-013, US-070, US-071)
- [ ] `US-029-T10` - Package Runtime PCF, host integration and operational support guidance (Deployment; size M; depends: US-001, US-002)

## Runtime board context and date navigation

### US-030 - Phase 2 - Read workspace - P0 / V1

Story: As a scheduler, I want to select a permitted board and date range so that I can work in the correct operational context.  
Dependencies: US-003, US-013, US-029, US-070  
Acceptance outcome: Only allowed boards show; active validated version loads; date navigation uses board timezone.

- [ ] `US-030-T01` - Implement board-context bootstrap (Technical; size L; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T02` - Build workspace command bar (UX; size L; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T03` - Implement timezone-safe navigation (Functional; size M; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T04` - Apply permitted-board filtering (Security; size M; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T05` - Fail closed on invalid board/version (Validation; size M; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T06` - Test context and timezone matrix (Testing; size L; depends: US-003, US-013, US-029, US-070)
- [ ] `US-030-T07` - Register solution component and release evidence (Deployment; size S; depends: US-003, US-013, US-029, US-070)

## Timeline and resource rows

### US-031 - Phase 2 - Read workspace - P0 / V1

Story: As a scheduler, I want a virtualised group/resource timeline with server paging so that large schedules remain usable.  
Dependencies: US-029, US-030  
Acceptance outcome: Only current page/viewport data loaded; request cancellation works; performance baseline met.

- [ ] `US-031-T01` - Implement read-model query contracts (Technical; size L; depends: US-029, US-030)
- [ ] `US-031-T02` - Build virtualised scheduler engine shell (Technical; size XL; depends: US-029, US-030)
- [ ] `US-031-T03` - Implement visible-slice cache and cancellation (Technical; size L; depends: US-029, US-030)
- [ ] `US-031-T04` - Design progressive load and empty/error states (UX; size M; depends: US-029, US-030)
- [ ] `US-031-T05` - Set performance budgets and instrumentation (Performance; size L; depends: US-029, US-030)
- [ ] `US-031-T06` - Run viewport/paging/performance tests (Testing; size XL; depends: US-029, US-030)
- [ ] `US-031-T07` - Register solution component and release evidence (Deployment; size S; depends: US-029, US-030)

## Filters and preferences

### US-032 - Phase 2 - Read workspace - P1 / V1

Story: As a scheduler, I want search, filters and saved non-sensitive preferences so that I can repeatedly focus on my work.  
Dependencies: US-030, US-031  
Acceptance outcome: Filter changes refresh correct slice; preference respects permissions/policy.

- [ ] `US-032-T01` - Define filter and preference model (Data; size M; depends: US-030, US-031)
- [ ] `US-032-T02` - Implement filter/search query composition (Functional; size L; depends: US-030, US-031)
- [ ] `US-032-T03` - Build accessible search/filter experience (UX; size L; depends: US-030, US-031)
- [ ] `US-032-T04` - Persist safe user preferences (Technical; size M; depends: US-030, US-031)
- [ ] `US-032-T05` - Validate configured filters (Validation; size M; depends: US-030, US-031)
- [ ] `US-032-T06` - Test search, persistence and permission cases (Testing; size L; depends: US-030, US-031)
- [ ] `US-032-T07` - Register solution component and release evidence (Deployment; size S; depends: US-030, US-031)

## Availability and overlay read model

### US-033 - Phase 2 - Read workspace - P1 / V1

Story: As a scheduler, I want overlays for availability, leave, work hours and holidays so that I can make safe scheduling choices.  
Dependencies: US-011, US-013, US-031  
Acceptance outcome: Configured overlays appear; missing mappings degrade safely; non-colour cues provided.

- [ ] `US-033-T01` - Define overlay mapping semantics (Data; size M; depends: US-011, US-013, US-031)
- [ ] `US-033-T02` - Implement overlay read and layout engine (Technical; size L; depends: US-011, US-013, US-031)
- [ ] `US-033-T03` - Design overlay legend and non-colour cues (UX; size M; depends: US-011, US-013, US-031)
- [ ] `US-033-T04` - Validate optional mapping and precedence (Validation; size M; depends: US-011, US-013, US-031)
- [ ] `US-033-T05` - Test timezone, DST and overlap cases (Testing; size L; depends: US-011, US-013, US-031)
- [ ] `US-033-T06` - Register solution component and release evidence (Deployment; size S; depends: US-011, US-013, US-031)

## Create and edit activity

### US-040 - Phase 3 - Core command runtime - P0 / V1

Story: As a scheduler, I want to create or edit a booking/activity with its own time so that I can schedule the actual work rather than only a parent record.  
Dependencies: US-011, US-012, US-071, US-070  
Acceptance outcome: Activity start/end independent; invalid interval rejected; parent context retained.

- [ ] `US-040-T01` - Define create/edit operation semantics (Functional; size L; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T02` - Build accessible booking/activity forms (UX; size L; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T03` - Implement validate/execute handling (Technical; size L; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T04` - Map defaults and managed fields (Data; size M; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T05` - Enforce interval and parent rules (Validation; size L; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T06` - Test create/edit paths (Testing; size L; depends: US-011, US-012, US-071, US-070)
- [ ] `US-040-T07` - Register solution component and release evidence (Deployment; size S; depends: US-011, US-012, US-071, US-070)

## Assign resources

### US-041 - Phase 3 - Core command runtime - P0 / V1

Story: As a scheduler, I want to assign one or more resources to an activity with roles so that group work is represented accurately.  
Dependencies: US-040, US-022, US-071  
Acceptance outcome: One activity supports multiple assignments; role compatibility validated; parent/sibling context visible.

- [ ] `US-041-T01` - Define assign/unassign/reassign semantics (Functional; size L; depends: US-040, US-022, US-071)
- [ ] `US-041-T02` - Build assignment controls (UX; size L; depends: US-040, US-022, US-071)
- [ ] `US-041-T03` - Implement assignment command handlers (Technical; size L; depends: US-040, US-022, US-071)
- [ ] `US-041-T04` - Resolve resource, role and activity mapping (Data; size M; depends: US-040, US-022, US-071)
- [ ] `US-041-T05` - Validate eligibility and capacity (Validation; size L; depends: US-040, US-022, US-071)
- [ ] `US-041-T06` - Test group-work cases (Testing; size L; depends: US-040, US-022, US-071)
- [ ] `US-041-T07` - Register solution component and release evidence (Deployment; size S; depends: US-040, US-022, US-071)

## Validation feedback and rule explanation

### US-051 - Phase 3 - Core command runtime - P0 / V1

Story: As a scheduler, I want blocking and warning conflicts explained before commit so that I can decide safely.  
Dependencies: US-022, US-070, US-071  
Acceptance outcome: Rule, severity, scope and message returned; warning needs confirmation when configured.

- [ ] `US-051-T01` - Define rule outcome contract (Data; size M; depends: US-022, US-070, US-071)
- [ ] `US-051-T02` - Implement rule pipeline (Technical; size XL; depends: US-022, US-070, US-071)
- [ ] `US-051-T03` - Build conflict and confirmation dialog (UX; size L; depends: US-022, US-070, US-071)
- [ ] `US-051-T04` - Secure confirmation tokens (Validation; size L; depends: US-022, US-070, US-071)
- [ ] `US-051-T05` - Test pass/warn/block behavior (Testing; size L; depends: US-022, US-070, US-071)
- [ ] `US-051-T06` - Capture rule diagnostics (Observability; size M; depends: US-022, US-070, US-071)
- [ ] `US-051-T07` - Register solution component and release evidence (Deployment; size S; depends: US-022, US-070, US-071)

## Move, resize and reassign

### US-042 - Phase 3 - Core command runtime - P0 / V1

Story: As a scheduler, I want to move, resize and reassign activities/assignments so that schedule changes are controlled and explained.  
Dependencies: US-040, US-041, US-051, US-071  
Acceptance outcome: Validate first; warn/confirm; execute with row version; affected scope refreshes.

- [ ] `US-042-T01` - Define move/resize/reassign delta rules (Functional; size L; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T02` - Implement drag, resize and form alternatives (UX; size XL; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T03` - Implement validate-confirm-execute orchestration (Technical; size L; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T04` - Evaluate affected graph and locks (Validation; size XL; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T05` - Test mutation, warning and stale paths (Testing; size XL; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T06` - Record operation evidence (Observability; size M; depends: US-040, US-041, US-051, US-071)
- [ ] `US-042-T07` - Register solution component and release evidence (Deployment; size S; depends: US-040, US-041, US-051, US-071)

## Assignment time override

### US-043 - Phase 3 - Core command runtime - P1 / V1

Story: As a scheduler, I want an assignment time override when the board permits it so that a resource can be scheduled for a portion of the activity.  
Dependencies: US-041, US-042  
Acceptance outcome: Override only appears when configured; rules enforce allowed boundary; inherited time remains default.

- [ ] `US-043-T01` - Add override mapping/policy (Data; size M; depends: US-041, US-042)
- [ ] `US-043-T02` - Define override lifecycle (Functional; size M; depends: US-041, US-042)
- [ ] `US-043-T03` - Provide override form and visual marker (UX; size M; depends: US-041, US-042)
- [ ] `US-043-T04` - Validate override boundaries (Validation; size M; depends: US-041, US-042)
- [ ] `US-043-T05` - Test override permutations (Testing; size M; depends: US-041, US-042)
- [ ] `US-043-T06` - Register solution component and release evidence (Deployment; size S; depends: US-041, US-042)

## Status model

### US-044 - Phase 3 - Core command runtime - P1 / V1

Story: As a scheduler, I want distinct booking, activity and assignment status transitions so that operational state is accurate at the right level.  
Dependencies: US-010, US-011, US-071  
Acceptance outcome: Independent configured transitions; forbidden transitions rejected; history audited.

- [ ] `US-044-T01` - Implement status models and transitions (Data; size L; depends: US-010, US-011, US-071)
- [ ] `US-044-T02` - Define transition policy (Functional; size M; depends: US-010, US-011, US-071)
- [ ] `US-044-T03` - Build status action experience (UX; size M; depends: US-010, US-011, US-071)
- [ ] `US-044-T04` - Enforce transitions in command service (Technical; size L; depends: US-010, US-011, US-071)
- [ ] `US-044-T05` - Test independent status state machines (Testing; size L; depends: US-010, US-011, US-071)
- [ ] `US-044-T06` - Register solution component and release evidence (Deployment; size S; depends: US-010, US-011, US-071)

## Requirement count and capacity state

### US-050 - Phase 3 - Core command runtime - P0 / V1

Story: As a scheduler, I want required versus allocated quantity/capacity for an activity so that I can see whether group work is complete.  
Dependencies: US-022, US-041  
Acceptance outcome: Eligible assignment statuses count correctly; shortfall/over-allocation displayed with text/icon.

- [ ] `US-050-T01` - Define completion and allocation measures (Data; size M; depends: US-022, US-041)
- [ ] `US-050-T02` - Implement shared requirement calculator (Technical; size L; depends: US-022, US-041)
- [ ] `US-050-T03` - Render accessible allocation indicators (UX; size M; depends: US-022, US-041)
- [ ] `US-050-T04` - Apply coverage rules (Validation; size M; depends: US-022, US-041)
- [ ] `US-050-T05` - Test calculation matrix (Testing; size L; depends: US-022, US-041)
- [ ] `US-050-T06` - Register solution component and release evidence (Deployment; size S; depends: US-022, US-041)

## Operation correlation and audit

### US-072 - Phase 4 - Audit/supportability - P1 / V1

Story: As a support analyst, I want correlation across UI, operation, audit, conflict and snapshot records so that I can diagnose an outcome end to end.  
Dependencies: US-071  
Acceptance outcome: Correlation query returns linked evidence without raw sensitive telemetry.

- [ ] `US-072-T01` - Define correlation and audit model (Data; size M; depends: US-071)
- [ ] `US-072-T02` - Implement structured operation/audit writes (Technical; size L; depends: US-071)
- [ ] `US-072-T03` - Provide support diagnostics view (UX; size M; depends: US-071)
- [ ] `US-072-T04` - Define privacy-safe telemetry schema (Observability; size M; depends: US-071)
- [ ] `US-072-T05` - Run traceability exercises (Testing; size L; depends: US-071)
- [ ] `US-072-T06` - Register solution component and release evidence (Deployment; size S; depends: US-071)

## Conflict and unscheduled workbenches

### US-052 - Phase 4 - Operational workbenches - P1 / V1

Story: As a scheduler, I want a conflict workbench so that I can triage unresolved issues without losing timeline context.  
Dependencies: US-051, US-072  
Acceptance outcome: Filter/sort/select; history retained; actions permission controlled.

- [ ] `US-052-T01` - Model persistent conflict cases (Data; size L; depends: US-051, US-072)
- [ ] `US-052-T02` - Create conflict read/query service (Technical; size M; depends: US-051, US-072)
- [ ] `US-052-T03` - Build conflict workbench (UX; size L; depends: US-051, US-072)
- [ ] `US-052-T04` - Implement resolution action policy (Functional; size M; depends: US-051, US-072)
- [ ] `US-052-T05` - Test conflict lifecycle and access (Testing; size L; depends: US-051, US-072)
- [ ] `US-052-T06` - Register solution component and release evidence (Deployment; size S; depends: US-051, US-072)

### US-053 - Phase 4 - Operational workbenches - P1 / V1

Story: As a scheduler, I want an unscheduled/partial workbench so that I can fill unassigned activities and incomplete requirements.  
Dependencies: US-050, US-041, US-031  
Acceptance outcome: Shows configured unassigned/partial work; open/assign actions available.

- [ ] `US-053-T01` - Define unscheduled/partial query criteria (Data; size M; depends: US-050, US-041, US-031)
- [ ] `US-053-T02` - Build workbench read model (Technical; size L; depends: US-050, US-041, US-031)
- [ ] `US-053-T03` - Build unscheduled/partial workbench (UX; size L; depends: US-050, US-041, US-031)
- [ ] `US-053-T04` - Connect workbench to assignment flow (Functional; size M; depends: US-050, US-041, US-031)
- [ ] `US-053-T05` - Test state changes and security (Testing; size L; depends: US-050, US-041, US-031)
- [ ] `US-053-T06` - Register solution component and release evidence (Deployment; size S; depends: US-050, US-041, US-031)

## Publish governance

### US-060 - Phase 4 - Publish governance - P0 / V1

Story: As a publish manager, I want to preview the resolved publish scope and blockers so that I do not publish an unsafe schedule.  
Dependencies: US-012, US-051, US-070, US-071  
Acceptance outcome: Scope, counts, warning/block, pending changes and lock policy displayed; server revalidates.

- [ ] `US-060-T01` - Define publish-scope resolution policy (Functional; size L; depends: US-012, US-051, US-070, US-071)
- [ ] `US-060-T02` - Implement publish preview command (Technical; size L; depends: US-012, US-051, US-070, US-071)
- [ ] `US-060-T03` - Build publish-preview workflow (UX; size L; depends: US-012, US-051, US-070, US-071)
- [ ] `US-060-T04` - Revalidate immediately before commit (Validation; size L; depends: US-012, US-051, US-070, US-071)
- [ ] `US-060-T05` - Test preview and scope edge cases (Testing; size L; depends: US-012, US-051, US-070, US-071)
- [ ] `US-060-T06` - Register solution component and release evidence (Deployment; size S; depends: US-012, US-051, US-070, US-071)

### US-061 - Phase 4 - Publish governance - P0 / V1

Story: As a publish manager, I want a successful publish to create immutable snapshots and locks so that official schedules are protected.  
Dependencies: US-060, US-072  
Acceptance outcome: Header/items created; managed fields included; lock rules enforced; audit linked.

- [ ] `US-061-T01` - Implement immutable snapshot structure (Data; size L; depends: US-060, US-072)
- [ ] `US-061-T02` - Implement transactional publish service (Technical; size XL; depends: US-060, US-072)
- [ ] `US-061-T03` - Enforce publish and lock permissions (Security; size M; depends: US-060, US-072)
- [ ] `US-061-T04` - Show publish result and official state (UX; size M; depends: US-060, US-072)
- [ ] `US-061-T05` - Test snapshot/lock atomicity (Testing; size XL; depends: US-060, US-072)
- [ ] `US-061-T06` - Define snapshot retention and operational runbook (Deployment; size M; depends: US-060, US-072)

### US-062 - Phase 4 - Publish governance - P0 / V1

Story: As a publish manager, I want governed rollback to a compatible prior snapshot so that I can recover the published schedule without overwriting unrelated data.  
Dependencies: US-061, US-012, US-072  
Acceptance outcome: Reason/permission required; only rollback-managed fields restored; new audit/result snapshot created.

- [ ] `US-062-T01` - Define compatible rollback policy (Functional; size L; depends: US-061, US-012, US-072)
- [ ] `US-062-T02` - Implement field-scoped rollback transaction (Technical; size XL; depends: US-061, US-012, US-072)
- [ ] `US-062-T03` - Build rollback preview and confirmation (UX; size L; depends: US-061, US-012, US-072)
- [ ] `US-062-T04` - Protect against unsafe restoration (Validation; size L; depends: US-061, US-012, US-072)
- [ ] `US-062-T05` - Test restoration boundaries (Testing; size XL; depends: US-061, US-012, US-072)
- [ ] `US-062-T06` - Publish rollback runbook (Documentation; size M; depends: US-061, US-012, US-072)

### US-063 - Phase 4 - Publish governance - P1 / V1

Story: As a scheduler, I want lock state and pending-change state visible so that I understand why a change is blocked or not yet official.  
Dependencies: US-060, US-061, US-031  
Acceptance outcome: Timeline/details show lock/pending badges and text; policy displayed.

- [ ] `US-063-T01` - Expose lock and pending-change read model (Technical; size M; depends: US-060, US-061, US-031)
- [ ] `US-063-T02` - Design status badges and explanatory details (UX; size M; depends: US-060, US-061, US-031)
- [ ] `US-063-T03` - Integrate state into action affordances (Functional; size M; depends: US-060, US-061, US-031)
- [ ] `US-063-T04` - Test state visibility and refresh (Testing; size M; depends: US-060, US-061, US-031)
- [ ] `US-063-T05` - Register solution component and release evidence (Deployment; size S; depends: US-060, US-061, US-031)

## Configuration Studio PCF completion

### US-014 - Phase 1 - Configuration experience - P0 / V1

Story: As a Configuration Administrator, I want a guided Planora Configuration Studio PCF so that I can create, edit, validate, preview, version and activate Schedule Board configurations without manually maintaining interdependent ccsb_* records.  
Dependencies: US-010, US-011, US-012, US-013, US-020, US-021, US-022, US-070, US-071  
Acceptance outcome: A Configuration Administrator can author draft versions through metadata-aware screens; active versions remain immutable; configuration validation, projection generation and activation use governed APIs; model-driven forms remain the support and low-level administration fallback.

- [ ] `US-014-T03` - Implement configuration session, draft state and lifecycle command facade (Technical; size L; depends: US-010, US-070, US-071)
- [ ] `US-014-T04` - Build metadata discovery and mapping designer (Technical; size XL; depends: US-011, US-012, US-070, US-071)
- [ ] `US-014-T05` - Implement grouping, roles, capability and requirement configuration modules (UX; size L; depends: US-020, US-021, US-022, US-070, US-071)
- [ ] `US-014-T06` - Implement status, rule and permission configuration modules (UX; size L; depends: US-010, US-011, US-070, US-071)
- [ ] `US-014-T07` - Implement compare, validate, projection and activation workbench (Validation; size XL; depends: US-010, US-011, US-012, US-013, US-020, US-022, US-070, US-071)
- [ ] `US-014-T08` - Enforce Configuration Studio authorisation, concurrency and audit policy (Security; size L; depends: US-070, US-071, US-072)
- [ ] `US-014-T09` - Complete Configuration Studio component, integration and accessibility tests (Testing; size XL; depends: US-010, US-011, US-012, US-013, US-020, US-022, US-070, US-071)
- [ ] `US-014-T10` - Validate metadata and draft-editor performance at enterprise configuration scale (Performance; size M; depends: US-011, US-013)
- [ ] `US-014-T11` - Package Configuration Studio, support fallback and administrator guidance (Deployment; size M; depends: US-001, US-002)

## Performance release evidence

### US-080 - Phase 5 - Release evidence - P0 / V1

Story: As a QA lead, I want performance tests at the reference profile so that the scheduler is released with measured scale evidence.  
Dependencies: US-031, US-042, US-060, US-061, US-062, US-072  
Acceptance outcome: Initial load, slice refresh, validation and interaction targets measured at 20 concurrent users.

- [ ] `US-080-T01` - Establish reference performance dataset (Performance; size L; depends: US-031, US-042, US-060, US-061, US-062, US-072)
- [ ] `US-080-T02` - Instrument client and server timings (Performance; size L; depends: US-031, US-042, US-060, US-061, US-062, US-072)
- [ ] `US-080-T03` - Build automated performance suite (Testing; size XL; depends: US-031, US-042, US-060, US-061, US-062, US-072)
- [ ] `US-080-T04` - Tune query, render and cache bottlenecks (Performance; size L; depends: US-031, US-042, US-060, US-061, US-062, US-072)
- [ ] `US-080-T05` - Publish performance limits and monitoring thresholds (Deployment; size M; depends: US-031, US-042, US-060, US-061, US-062, US-072)

## Accessibility release evidence

### US-081 - Phase 5 - Release evidence - P0 / V1

Story: As an accessibility specialist, I want task-based keyboard and assistive-technology validation so that all core scheduling functions are usable without drag/drop.  
Dependencies: US-030, US-031, US-040, US-041, US-042, US-060, US-062  
Acceptance outcome: Focused tests cover selection, forms, commands, errors, publish and rollback.

- [ ] `US-081-T01` - Create accessibility interaction specification (UX; size L; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)
- [ ] `US-081-T02` - Implement semantic/focus foundations (Technical; size XL; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)
- [ ] `US-081-T03` - Provide non-colour status representation (UX; size M; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)
- [ ] `US-081-T04` - Run automated accessibility checks (Testing; size L; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)
- [ ] `US-081-T05` - Run manual assistive-technology scenarios (Testing; size XL; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)
- [ ] `US-081-T06` - Register solution component and release evidence (Deployment; size S; depends: US-030, US-031, US-040, US-041, US-042, US-060, US-062)

## Upgrade rehearsal and support runbook

### US-082 - Phase 5 - Release evidence - P1 / V1

Story: As a release manager, I want an upgrade rehearsal and support runbook so that configuration and operational issues are recoverable.  
Dependencies: US-001, US-002, US-013, US-061, US-062, US-080, US-081  
Acceptance outcome: Managed import/compatibility/rollback rehearsed; support workflows signed off.

- [ ] `US-082-T01` - Define release/upgrade rehearsal plan (Deployment; size M; depends: US-001, US-002, US-013, US-061, US-062, US-080, US-081)
- [ ] `US-082-T02` - Execute upgrade and rollback rehearsals (Testing; size XL; depends: US-001, US-002, US-013, US-061, US-062, US-080, US-081)
- [ ] `US-082-T03` - Create operational support runbook (Documentation; size L; depends: US-001, US-002, US-013, US-061, US-062, US-080, US-081)
- [ ] `US-082-T04` - Set release gates and health checks (Observability; size M; depends: US-001, US-002, US-013, US-061, US-062, US-080, US-081)
- [ ] `US-082-T05` - Produce release notes and customer guidance (Deployment; size M; depends: US-001, US-002, US-013, US-061, US-062, US-080, US-081)

## Deferred split/merge design gate

### US-090 - Deferred - Design gate - Later / Later

Story: As a scheduler, I want split/merge operations so that work can be decomposed or combined with governed graph semantics.  
Dependencies: US-062, US-082  
Acceptance outcome: Not V1. Requires design approval for event graph, audit, publish and rollback semantics.

- [ ] `US-090-T01` - Retain as deferred V1 item (Discovery; size S; depends: US-062, US-082)
- [ ] `US-090-T02` - Create future graph-mutation design gate (Architecture; size M; depends: US-062, US-082)
- [ ] `US-090-T03` - Define future regression charter (Testing; size S; depends: US-062, US-082)

## Deferred mobile/offline design gate

### US-091 - Deferred - Design gate - Later / Later

Story: As a mobile user, I want offline scheduling so that I can work without connectivity.  
Dependencies: US-082  
Acceptance outcome: Not V1. Requires mobile/offline profile, synchronization, conflict policy and dedicated NFR baseline.

- [ ] `US-091-T01` - Retain offline/mobile as deferred V1 item (Discovery; size S; depends: US-082)
- [ ] `US-091-T02` - Create mobile/offline feasibility design (Architecture; size L; depends: US-082)
- [ ] `US-091-T03` - Define field-sync test charter (Testing; size M; depends: US-082)

## Deferred connectors design gate

### US-092 - Deferred - Design gate - Later / Later

Story: As an integration owner, I want outbound connectors so that schedule changes can inform other platforms.  
Dependencies: US-071, US-072, US-082  
Acceptance outcome: Not V1. Requires outbox delivery, retries, idempotency, security and monitoring design.

- [ ] `US-092-T01` - Retain connectors as deferred V1 item (Discovery; size S; depends: US-071, US-072, US-082)
- [ ] `US-092-T02` - Define outbox and delivery contract (Architecture; size L; depends: US-071, US-072, US-082)
- [ ] `US-092-T03` - Define connector reliability suite (Testing; size M; depends: US-071, US-072, US-082)

## Deferred URS and enterprise adapter design gate

### US-093 - Deferred - Design gate - Later / Later

Story: As an enterprise user, I want URS/Field Service/Project Operations adapters so that selected data can interoperate.  
Dependencies: US-011, US-071, US-082  
Acceptance outcome: Not V1. Requires licensed contract, regression and support matrix.

- [ ] `US-093-T01` - Retain adapters as deferred V1 item (Discovery; size S; depends: US-011, US-071, US-082)
- [ ] `US-093-T02` - Assess licensed adapter contracts (Architecture; size L; depends: US-011, US-071, US-082)
- [ ] `US-093-T03` - Define interoperability regression charter (Testing; size M; depends: US-011, US-071, US-082)

## Coverage check

- Source user stories: 40
- Source tasks: 249
- Tasks in full ordered sequence: 249
- Duplicate placements avoided: 0
- Missing tasks: none

## Release 1 scope guardrails

- Do not expand Release 1 into generic customer-table mapping; the native graph from `US-004-T04` is the proof path.
- Do not complete the Configuration Studio PCF before the Runtime PCF proves which configuration properties matter.
- Do not implement publish/rollback, split/merge, mobile/offline, external connectors or URS adapters inside the first runtime demo.
- Do not claim production readiness until separate test/UAT validation, managed-solution rehearsal, formal accessibility evidence, performance evidence and support runbooks are complete.
