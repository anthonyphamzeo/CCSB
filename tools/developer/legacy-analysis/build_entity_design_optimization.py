from __future__ import annotations

import csv
import html
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "docs" / "design" / "data-model" / "physical-schema"
OUT_HTML = OUT_DIR / "ccsb-optimized-database-design-evidence-v1_1.html"
OUT_CHANGES = OUT_DIR / "ccsb-optimized-design-change-log-v1_1.csv"
PREVIOUS_FIELD_CSV = OUT_DIR / "ccsb-proposed-field-inventory.csv"
PREVIOUS_REL_CSV = OUT_DIR / "ccsb-proposed-relationship-inventory.csv"

PLUS_DESIGN = r"C:/Users/Anthony/Downloads/CCSB_Entity_Design_and_Canonical_Inventory_v1_0.html"
COMPARISON_DOC = r"C:/Users/Anthony/Downloads/CCSB_Entity_Design_Comparison_and_Hybrid_Recommendation_v1_0.html"
CODEX_PREVIOUS = "docs/design/data-model/physical-schema/ccsb-entity-design-canonical-inventory-validation.html"


MICROSOFT_SOURCES = [
    {
        "label": "Table definitions in Microsoft Dataverse",
        "url": "https://learn.microsoft.com/en-us/power-apps/developer/data-platform/entity-metadata",
        "evidence": "Custom table logical names are lower case, custom table names cannot be changed after creation except entity set name, and new tables can only be Organization or User/Team owned. Ownership cannot be changed after creation.",
        "design_use": "Freeze the ownership matrix before import; use ccsb_ logical names; keep business lifecycle fields separate from statecode/statuscode.",
    },
    {
        "label": "Configure table relationship cascading behavior",
        "url": "https://learn.microsoft.com/en-us/power-apps/developer/data-platform/configure-entity-relationship-cascading-behavior",
        "evidence": "Dataverse supports NoCascade, Restrict, RemoveLink, Cascade, Active, and UserOwned cascade behavior; Restrict prevents parent deletion when child rows exist.",
        "design_use": "Use Restrict delete and NoCascade for governance, evidence, lock, snapshot, and outbox relationships.",
    },
    {
        "label": "Work with alternate keys",
        "url": "https://learn.microsoft.com/en-us/power-apps/developer/data-platform/define-alternate-keys-entity",
        "evidence": "Alternate keys uniquely identify rows by business columns, are limited by key size and count, cannot use field-level-secured attributes, and special characters in key values can break GET/PATCH/upsert integration usage.",
        "design_use": "Use sanitized durable keys only; never make transient tokens such as lock tokens alternate keys.",
    },
    {
        "label": "Column-level security",
        "url": "https://learn.microsoft.com/en-us/power-platform/admin/field-level-security",
        "evidence": "Column security controls read, create, and update permissions for sensitive columns, but lookup columns, primary name columns, system columns, virtual table columns, and formula columns cannot be secured.",
        "design_use": "Secure JSON payload, reason, diagnostic, and error fields; do not attempt to secure lookup, primary name, status, or alternate key columns.",
    },
    {
        "label": "Manage Dataverse auditing",
        "url": "https://learn.microsoft.com/en-us/power-platform/admin/manage-dataverse-auditing",
        "evidence": "Auditing is configured at environment, table, and column levels, logs create/update/delete and sharing changes, consumes log storage, has retention behavior, and does not audit definition changes or retrieve/export operations.",
        "design_use": "Use Dataverse audit for platform history, but keep ccsb_operationaudit for product semantics, policy, correlation, and reason evidence.",
    },
    {
        "label": "Create and use custom APIs",
        "url": "https://learn.microsoft.com/en-us/power-apps/developer/data-platform/custom-api",
        "evidence": "Custom APIs can consolidate operations callable from code or Power Automate, usually combine with plug-ins, can require an execute privilege, and managed API components should be non-customizable.",
        "design_use": "Route schedule writes, publish, rollback, lock, and outbox creation through governed APIs rather than direct table edits.",
    },
    {
        "label": "Project schedule APIs",
        "url": "https://learn.microsoft.com/en-us/dynamics365/project-operations/project-management/schedule-api-preview",
        "evidence": "Project schedule APIs create, update, and delete scheduling entities through the Project scheduling engine; operation sets execute multiple schedule operations as a unit.",
        "design_use": "Use adapter and operation/correlation fields instead of hard-coding direct CRUD assumptions for Project Operations entities.",
    },
    {
        "label": "Field Service Resource Requirement table",
        "url": "https://learn.microsoft.com/en-us/dynamics365/field-service/developer/reference/entities/msdyn_resourcerequirement",
        "evidence": "The Field Service resource requirement table is UserOwned and includes resource type, duration, effort, percentage capacity, territory, and time-window concepts.",
        "design_use": "Align requirement and capability concepts to Field Service vocabulary without making CCSB depend on msdyn_ tables being installed.",
    },
]


def f(name: str, dtype: str, purpose: str, required: str = "No", security: str = "Standard", constraint: str = "") -> dict[str, str]:
    return {
        "logical": name,
        "type": dtype,
        "required": required,
        "purpose": purpose,
        "security": security,
        "constraint": constraint,
    }


def r(source: str, lookup: str, target: str, why: str, required: str = "No", cascade: str = "Delete Restrict; assign/share/reparent NoCascade") -> dict[str, str]:
    return {
        "source": source,
        "lookup": lookup,
        "target": target,
        "required": required,
        "cascade": cascade,
        "why": why,
    }


ENTITIES: list[dict] = [
    {
        "logical": "ccsb_resourcecapability",
        "display": "Resource Capability",
        "ownership": "UserOwned",
        "previous_codex": "UserOwned",
        "plus": "OrganizationOwned",
        "decision": "Keep user/team ownership. Resource capability rows are operationally close to bookable resources and should honor row-level resource stewardship.",
        "keys": ["ccsb_capabilitykey"],
        "audit": "Enable Dataverse audit on business columns. Do not secure alternate-key columns.",
        "fields": [
            f("ccsb_resourcecapabilityid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Lookup display name for forms and views.", "Yes", constraint="Max 300."),
            f("ccsb_capabilitykey", "Text", "Stable sanitized identity for upsert and dedupe.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_resourceid", "Lookup", "CCSB resource that owns the capability.", "Runtime required"),
            f("ccsb_resourceroleid", "Lookup", "Optional role context when a capability varies by role."),
            f("ccsb_capabilitytype", "Choice", "Domain: skill, certification, clearance, territory, facility feature, equipment, capacity, custom.", "Yes"),
            f("ccsb_capabilitycode", "Text", "Canonical capability code used by rule matching.", "Yes", constraint="Max 100."),
            f("ccsb_capabilitysource", "Choice", "Source domain: CCSB, Field Service, Project Operations, external, manual.", "Yes"),
            f("ccsb_externalkey", "Text", "External/source-system identity when imported.", constraint="Max 200."),
            f("ccsb_sourcetablelogicalname", "Text", "Optional source table logical name for adapter traceability.", constraint="Max 128."),
            f("ccsb_sourcerecordid", "Text", "Optional source record identifier.", constraint="Max 100."),
            f("ccsb_effectivefrom", "DateTime", "Start of eligibility window."),
            f("ccsb_effectiveto", "DateTime", "End of eligibility window."),
            f("ccsb_proficiencylevel", "Choice", "Coarse proficiency/rating band."),
            f("ccsb_proficiencyvalue", "Decimal", "Numeric proficiency score where a source uses values instead of bands."),
            f("ccsb_capacityunits", "Decimal", "Capability capacity contribution or allocation units."),
            f("ccsb_verificationstatus", "Choice", "Unverified, verified, expired, rejected, waived."),
            f("ccsb_verifiedon", "DateTime", "When the capability evidence was verified."),
            f("ccsb_verifiedby", "Lookup systemuser", "User who verified the evidence."),
            f("ccsb_expirydate", "DateTime", "Certification or eligibility expiry date."),
            f("ccsb_iseligible", "Boolean", "Computed or imported final eligibility flag used by scheduling rules.", "Yes"),
            f("ccsb_capabilitystatus", "Choice", "Active, inactive, superseded, archived."),
            f("ccsb_sourcehash", "Text", "Hash of source capability input for drift checks.", constraint="Max 128."),
            f("ccsb_notes", "Multiline Text", "Short steward notes. Keep sensitive evidence outside alternate keys.", security="Field security recommended"),
        ],
        "defer": [
            "ccsb_proficiencymodel and ccsb_proficiencylabel: add only when multiple scoring models are actually configured.",
            "ccsb_isprimary: defer unless UI or rules need a single preferred capability in a group.",
            "ccsb_capabilitydefinition: future normalized taxonomy table if reusable capability governance becomes larger than one table can carry.",
        ],
    },
    {
        "logical": "ccsb_operationaudit",
        "display": "Operation Audit",
        "ownership": "OrganizationOwned",
        "previous_codex": "UserOwned",
        "plus": "OrganizationOwned",
        "decision": "Change from Codex previous design to organization-owned. Audit evidence should not inherit a user owner that could change access or business unit behavior.",
        "keys": ["ccsb_auditeventkey"],
        "audit": "Enable Dataverse audit, but treat this table as the product audit ledger. Updates should be limited to retention/archive metadata.",
        "fields": [
            f("ccsb_operationauditid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Short event title.", "Yes", constraint="Max 300."),
            f("ccsb_auditeventkey", "Text", "Durable event identity, derived from operation id plus sequence.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_operationid", "Lookup", "Operation header that caused the event."),
            f("ccsb_operationitemid", "Lookup", "Operation item when the event is item-specific."),
            f("ccsb_sequence", "Whole Number", "Monotonic order within the operation.", "Yes"),
            f("ccsb_schedulechangeid", "Lookup", "Schedule change related to the event."),
            f("ccsb_publishsnapshotid", "Lookup", "Publish snapshot related to the event."),
            f("ccsb_publishlockid", "Lookup", "Publish lock related to the event."),
            f("ccsb_actorid", "Lookup systemuser", "Interactive or application user represented in Dataverse."),
            f("ccsb_actorprincipaltype", "Choice", "User, team, application user, system, integration."),
            f("ccsb_actorprincipalid", "Text", "External principal identifier if not represented by systemuser.", constraint="Max 200."),
            f("ccsb_auditeventtype", "Choice", "Validation, command, security, publish, rollback, lock, integration, support, system."),
            f("ccsb_actiontype", "Choice", "Create, update, delete, approve, reject, publish, rollback, lock, unlock, dispatch."),
            f("ccsb_outcome", "Choice", "Started, succeeded, failed, blocked, skipped, compensated."),
            f("ccsb_severity", "Choice", "Information, warning, error, critical."),
            f("ccsb_correlationid", "Text", "Cross-table and cross-service correlation identifier.", constraint="Max 100."),
            f("ccsb_causationid", "Text", "Parent event or message id.", constraint="Max 100."),
            f("ccsb_idempotencykey", "Text", "Idempotency key supplied by API or worker.", constraint="Max 200."),
            f("ccsb_apioperation", "Text", "Custom API, plug-in, flow, or integration operation name.", constraint="Max 200."),
            f("ccsb_apiversion", "Text", "Contract version of the operation.", constraint="Max 50."),
            f("ccsb_targetscopetype", "Choice", "Board, version, requirement, assignment, resource, group, external."),
            f("ccsb_targetreferenceid", "Text", "Record id or scope key affected by the action.", constraint="Max 100."),
            f("ccsb_reasoncategory", "Choice", "Policy, user request, conflict, integration, data correction, support, system."),
            f("ccsb_reasontext", "Multiline Text", "User-visible business reason, override reason, or support note.", security="Field security recommended"),
            f("ccsb_errorcode", "Text", "Stable error code.", constraint="Max 100."),
            f("ccsb_errordetail", "Multiline Text", "Diagnostic detail, sanitized before storage.", security="Field security recommended"),
            f("ccsb_occurredon", "DateTime", "UTC timestamp when the event occurred.", "Yes"),
            f("ccsb_policyversion", "Text", "Rule/policy version that governed the decision.", constraint="P1 if policy engine versioning is not ready."),
            f("ccsb_diagnosticjson", "Multiline Text", "Structured diagnostics for support, never used as the canonical business payload.", security="Field security recommended", constraint="P1 or secure-only."),
            f("ccsb_previousrecordhash", "Text", "Optional hash-chain pointer for tamper-evidence.", constraint="P1; max 128."),
            f("ccsb_recordhash", "Text", "Hash of immutable event payload fields.", constraint="Max 128."),
            f("ccsb_retentionuntil", "DateTime", "Retention/archive boundary for support operations."),
        ],
        "defer": [
            "Full before/after/delta images in operationaudit. Keep them in schedulechange or publishsnapshotitem so audit stays searchable and bounded.",
            "High-volume plug-in trace details. Use Dataverse plug-in trace/Application Insights and store only sanitized references here.",
        ],
    },
    {
        "logical": "ccsb_schedulechange",
        "display": "Schedule Change",
        "ownership": "OrganizationOwned",
        "previous_codex": "UserOwned",
        "plus": "OrganizationOwned",
        "decision": "Change from Codex previous design to organization-owned. This table is a product ledger for mutations, not personal work owned by the requester.",
        "keys": ["ccsb_changekey"],
        "audit": "Enable auditing. State transitions should be controlled by Custom APIs and plug-ins.",
        "fields": [
            f("ccsb_schedulechangeid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Readable change summary.", "Yes", constraint="Max 300."),
            f("ccsb_changekey", "Text", "Stable idempotent identity for the schedule mutation.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_boardid", "Lookup", "Board affected by the change."),
            f("ccsb_boardversionid", "Lookup", "Planning version affected by the change."),
            f("ccsb_scheduleversionid", "Lookup", "Schedule version affected by the change."),
            f("ccsb_scheduleitemid", "Lookup", "Schedule item affected by the change."),
            f("ccsb_scheduleassignmentid", "Lookup", "Assignment affected by the change."),
            f("ccsb_schedulerequirementid", "Lookup", "Requirement affected by the change."),
            f("ccsb_resourceid", "Lookup", "Resource affected by the change."),
            f("ccsb_operationid", "Lookup", "Command/operation that requested the change."),
            f("ccsb_operationitemid", "Lookup", "Operation item that requested the change."),
            f("ccsb_publishlockid", "Lookup", "Lock checked or acquired for this mutation."),
            f("ccsb_correlationid", "Text", "Cross-table correlation id.", constraint="Max 100."),
            f("ccsb_changetype", "Choice", "Create, update, delete, move, assign, unassign, split, merge, rollback, publish."),
            f("ccsb_changestatus", "Choice", "Proposed, validated, approved, committed, published, rejected, superseded, rolled back, failed."),
            f("ccsb_sourceorigin", "Choice", "User, API, bulk import, optimizer, external integration, rollback, system."),
            f("ccsb_sourceentitylogicalname", "Text", "Source table logical name for imported or adapter-created changes.", constraint="Max 128."),
            f("ccsb_sourcerecordid", "Text", "Source record identifier.", constraint="Max 100."),
            f("ccsb_targetentitylogicalname", "Text", "Target Dataverse table logical name.", constraint="Max 128."),
            f("ccsb_targetrecordid", "Text", "Target record id expected to be mutated.", constraint="Max 100."),
            f("ccsb_expectedrowversion", "Text", "Concurrency value observed before the write.", constraint="Max 100."),
            f("ccsb_fieldscopejson", "Multiline Text", "Managed field list touched by the change.", security="Field security recommended"),
            f("ccsb_beforepayloadjson", "Multiline Text", "Before image for managed rollback scope.", security="Field security recommended"),
            f("ccsb_proposedpayloadjson", "Multiline Text", "Proposed write payload before transformation.", "Yes", "Field security recommended"),
            f("ccsb_committedpayloadjson", "Multiline Text", "Actual committed payload if different from proposal.", security="Field security recommended", constraint="Required only for partial or transformed commits."),
            f("ccsb_rollbackimagejson", "Multiline Text", "Rollback image for managed fields.", security="Field security recommended"),
            f("ccsb_ruleoutcomejson", "Multiline Text", "Validation and policy result summary.", security="Field security recommended"),
            f("ccsb_requiresapproval", "Boolean", "Whether the change requires approval."),
            f("ccsb_approvedby", "Lookup systemuser", "Approver for governed change."),
            f("ccsb_approvedon", "DateTime", "Approval timestamp."),
            f("ccsb_overridereason", "Multiline Text", "Business reason for override.", security="Field security recommended"),
            f("ccsb_requestedby", "Lookup systemuser", "Requester represented in Dataverse."),
            f("ccsb_requestedon", "DateTime", "UTC request timestamp.", "Yes"),
            f("ccsb_committedon", "DateTime", "UTC commit timestamp."),
            f("ccsb_publishedon", "DateTime", "UTC publish timestamp."),
            f("ccsb_changehash", "Text", "Hash of core change payload.", constraint="Max 128."),
            f("ccsb_isrollbackcandidate", "Boolean", "Whether rollback tooling may use this change."),
            f("ccsb_retentionuntil", "DateTime", "Retention/archive boundary."),
        ],
        "defer": [
            "Direct conflict, publishsnapshotitem, and predecessor lookups. Use operation and correlation first; add direct links when navigation or query volume proves the need.",
            "ccsb_changestate. Use ccsb_changestatus to avoid confusion with Dataverse statecode.",
        ],
    },
    {
        "logical": "ccsb_publishsnapshotitem",
        "display": "Publish Snapshot Item",
        "ownership": "OrganizationOwned",
        "previous_codex": "OrganizationOwned",
        "plus": "OrganizationOwned",
        "decision": "Keep organization-owned. Snapshot items are immutable evidence, not user-owned work records.",
        "keys": ["ccsb_snapshotitemkey"],
        "audit": "Enable auditing. Deny update/delete except archive tooling.",
        "fields": [
            f("ccsb_publishsnapshotitemid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Readable snapshot item name.", "Yes", constraint="Max 300."),
            f("ccsb_snapshotitemkey", "Text", "Stable snapshot item identity.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_publishsnapshotid", "Lookup", "Snapshot header.", "Yes"),
            f("ccsb_sequence", "Whole Number", "Order inside the snapshot.", "Yes"),
            f("ccsb_snapshotitemtype", "Choice", "Schedule item, assignment, requirement, resource, lock, metadata, external projection."),
            f("ccsb_capturestatus", "Choice", "Captured, skipped, missing, transformed, failed."),
            f("ccsb_schedulechangeid", "Lookup", "Change that produced or is protected by this item."),
            f("ccsb_scheduleitemid", "Lookup", "Schedule item captured."),
            f("ccsb_scheduleassignmentid", "Lookup", "Assignment captured."),
            f("ccsb_schedulerequirementid", "Lookup", "Requirement captured."),
            f("ccsb_resourceid", "Lookup", "Resource captured."),
            f("ccsb_sourceentitylogicalname", "Text", "Logical name of the captured table.", constraint="Max 128."),
            f("ccsb_sourcerecordid", "Text", "Captured record identifier.", constraint="Max 100."),
            f("ccsb_sourceversion", "Text", "Row version or source version at capture time.", constraint="Max 100."),
            f("ccsb_managedfieldscopejson", "Multiline Text", "Fields governed by rollback and official-state comparison.", security="Field security recommended"),
            f("ccsb_payloadjson", "Multiline Text", "Captured payload for the managed field scope.", "Yes", "Field security recommended"),
            f("ccsb_payloadhash", "Text", "Hash of captured payload.", "Yes", constraint="Max 128."),
            f("ccsb_rollbackimagejson", "Multiline Text", "Optional rollback-specific image if it differs from payload.", security="Field security recommended"),
            f("ccsb_isdeletedatcapture", "Boolean", "Whether source row was deleted or absent at capture time."),
            f("ccsb_isimmutable", "Boolean", "Marks the item as immutable after snapshot close.", "Yes"),
            f("ccsb_retentionuntil", "DateTime", "Retention/archive boundary."),
        ],
        "defer": [
            "Duplicate board, version, operation, and actor fields already available from the snapshot header unless reporting proves a denormalized read requirement.",
            "Relationship context and predecessor hash. Add in P1 for hash-chain lineage or differential publish features.",
        ],
    },
    {
        "logical": "ccsb_publishlock",
        "display": "Publish Lock",
        "ownership": "OrganizationOwned",
        "previous_codex": "UserOwned",
        "plus": "OrganizationOwned",
        "decision": "Change from Codex previous design to organization-owned. A publish lock is a board protection record, not an owned personal row or worker lease.",
        "keys": ["ccsb_lockkey"],
        "audit": "Enable auditing. Lock/unlock/override must be Custom API operations.",
        "fields": [
            f("ccsb_publishlockid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Readable lock name.", "Yes", constraint="Max 300."),
            f("ccsb_lockkey", "Text", "Stable lock identity for scope and idempotency.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_boardid", "Lookup", "Board protected by the lock."),
            f("ccsb_boardversionid", "Lookup", "Board version protected by the lock."),
            f("ccsb_scheduleversionid", "Lookup", "Schedule version protected by the lock."),
            f("ccsb_publishsnapshotid", "Lookup", "Snapshot or publish event that created the lock."),
            f("ccsb_operationid", "Lookup", "Operation that acquired the lock."),
            f("ccsb_groupnodeid", "Lookup", "Requirement group or board node in scope."),
            f("ccsb_resourceid", "Lookup", "Resource in scope."),
            f("ccsb_scheduleitemid", "Lookup", "Schedule item in scope."),
            f("ccsb_locktype", "Choice", "Publish protection, edit freeze, rollback protection, approval hold, external dependency."),
            f("ccsb_locklevel", "Choice", "Board, version, group, resource, item, field, external."),
            f("ccsb_lockstatus", "Choice", "Active, released, expired, overridden, superseded."),
            f("ccsb_scopetype", "Choice", "Global board, time window, resource, requirement, assignment, external."),
            f("ccsb_scopefromutc", "DateTime", "Optional scope start time."),
            f("ccsb_scopetoutc", "DateTime", "Optional scope end time."),
            f("ccsb_timezoneid", "Text", "Timezone used to interpret business scope.", constraint="Max 100."),
            f("ccsb_scopecriteriajson", "Multiline Text", "Structured scope criteria.", security="Field security recommended"),
            f("ccsb_protectedactionsjson", "Multiline Text", "Actions blocked or allowed by the lock.", security="Field security recommended"),
            f("ccsb_lockedby", "Lookup systemuser", "User or app user that acquired the lock."),
            f("ccsb_lockedon", "DateTime", "UTC lock acquisition timestamp.", "Yes"),
            f("ccsb_expireson", "DateTime", "Business expiration time, not a worker heartbeat."),
            f("ccsb_releasedby", "Lookup systemuser", "User or app user that released the lock."),
            f("ccsb_releasedon", "DateTime", "UTC release timestamp."),
            f("ccsb_overriddenby", "Lookup systemuser", "User authorized to override the lock."),
            f("ccsb_overriddenon", "DateTime", "UTC override timestamp."),
            f("ccsb_overridereason", "Multiline Text", "Governed reason for override.", security="Field security recommended"),
            f("ccsb_supersedeslockid", "Lookup ccsb_publishlock", "Previous lock superseded by this one."),
            f("ccsb_correlationid", "Text", "Correlation id across lock and publish operations.", constraint="Max 100."),
            f("ccsb_isactive", "Boolean", "Fast query flag for active lock views."),
            f("ccsb_retentionuntil", "DateTime", "Retention/archive boundary."),
        ],
        "defer": [
            "ccsb_locktoken as an alternate key. A token is transient and can contain unsafe characters; keep it out of durable identity.",
            "Worker heartbeat, lease owner, and claim fields. If a queue worker lease is needed, create ccsb_operationlease or use outbox claim fields rather than mixing lease semantics into publishlock.",
        ],
    },
    {
        "logical": "ccsb_outboxevent",
        "display": "Outbox Event",
        "ownership": "OrganizationOwned",
        "previous_codex": "OrganizationOwned",
        "plus": "OrganizationOwned",
        "decision": "Keep organization-owned. Outbox rows are durable integration work items and should not depend on a user owner.",
        "keys": ["ccsb_eventkey"],
        "audit": "Enable audit on status, attempt, and error fields. Payload fields should be secured and retention-managed.",
        "fields": [
            f("ccsb_outboxeventid", "Uniqueidentifier", "Primary Dataverse identifier.", "System"),
            f("ccsb_name", "Primary Name", "Readable event name.", "Yes", constraint="Max 300."),
            f("ccsb_eventkey", "Text", "Durable event identity for idempotent delivery.", "Yes", constraint="Alternate key; max 200."),
            f("ccsb_eventtype", "Choice", "Published, changed, locked, unlocked, rollback, export, notification, integration command."),
            f("ccsb_eventversion", "Text", "Event contract version.", "Yes", constraint="Max 50."),
            f("ccsb_eventstatus", "Choice", "Pending, processing, delivered, failed, dead-lettered, skipped, replayed."),
            f("ccsb_boardid", "Lookup", "Board context."),
            f("ccsb_boardversionid", "Lookup", "Board version context."),
            f("ccsb_scheduleversionid", "Lookup", "Schedule version context."),
            f("ccsb_operationid", "Lookup", "Operation that produced the event."),
            f("ccsb_schedulechangeid", "Lookup", "Schedule change that produced the event."),
            f("ccsb_publishsnapshotid", "Lookup", "Snapshot that produced the event."),
            f("ccsb_publishlockid", "Lookup", "Lock that produced the event."),
            f("ccsb_correlationid", "Text", "Cross-system correlation id.", constraint="Max 100."),
            f("ccsb_causationid", "Text", "Message or event that caused this event.", constraint="Max 100."),
            f("ccsb_idempotencykey", "Text", "Consumer or producer idempotency key.", constraint="Max 200."),
            f("ccsb_aggregateentitylogicalname", "Text", "Aggregate table for ordered event streams.", constraint="Max 128."),
            f("ccsb_aggregaterecordid", "Text", "Aggregate record id.", constraint="Max 100."),
            f("ccsb_aggregatesequence", "Whole Number", "Per-aggregate sequence for ordered delivery."),
            f("ccsb_partitionkey", "Text", "Partition/shard key for delivery workers.", constraint="Max 200."),
            f("ccsb_destinationtype", "Choice", "Dataverse event, Power Automate, Service Bus, Event Grid, webhook, export, internal."),
            f("ccsb_destinationkey", "Text", "Logical destination configuration key; never raw URL, token, or secret.", constraint="Max 200."),
            f("ccsb_topic", "Text", "Topic or channel name.", constraint="Max 200."),
            f("ccsb_payloadcontenttype", "Text", "Payload content type.", constraint="Max 100."),
            f("ccsb_payloadjson", "Multiline Text", "Event body, sanitized and bounded.", "Yes", "Field security recommended"),
            f("ccsb_payloadhash", "Text", "Hash of event payload.", constraint="Max 128."),
            f("ccsb_payloadsizebytes", "Whole Number", "Serialized payload size for monitoring."),
            f("ccsb_occurredon", "DateTime", "Business event timestamp.", "Yes"),
            f("ccsb_availableon", "DateTime", "Earliest delivery time."),
            f("ccsb_lockeduntil", "DateTime", "Transient claim timeout for delivery worker."),
            f("ccsb_locktoken", "Text", "Transient delivery claim token, not an alternate key.", constraint="Max 200."),
            f("ccsb_attemptcount", "Whole Number", "Number of delivery attempts."),
            f("ccsb_maxattempts", "Whole Number", "Maximum attempts before dead letter."),
            f("ccsb_retryafter", "DateTime", "Next retry time."),
            f("ccsb_lastattempton", "DateTime", "Most recent attempt timestamp."),
            f("ccsb_deliveredon", "DateTime", "Successful delivery timestamp."),
            f("ccsb_errorcode", "Text", "Last stable delivery error code.", constraint="Max 100."),
            f("ccsb_errordetail", "Multiline Text", "Sanitized delivery error detail.", security="Field security recommended"),
            f("ccsb_deadletterreason", "Multiline Text", "Governed reason event moved to dead letter.", security="Field security recommended"),
            f("ccsb_isreplayable", "Boolean", "Whether governed replay is allowed."),
            f("ccsb_retentionuntil", "DateTime", "Retention/archive boundary."),
        ],
        "defer": [
            "Raw endpoint URLs, connection strings, tokens, SAS URLs, or secrets. Resolve destinationkey through secure configuration outside this table.",
            "Delivery enablement. Persist the outbox in P0; turn on external dispatch only after retry, dead-letter, and monitoring runbooks exist.",
        ],
    },
]


RELATIONSHIPS = [
    r("ccsb_resourcecapability", "ccsb_resourceid", "ccsb_resource", "Resource capability belongs to a CCSB resource.", "Runtime required"),
    r("ccsb_resourcecapability", "ccsb_resourceroleid", "ccsb_resourcerole", "Optional role-specific capability context."),
    r("ccsb_resourcecapability", "ccsb_verifiedby", "systemuser", "Verification accountability."),
    r("ccsb_operationaudit", "ccsb_operationid", "ccsb_operation", "Audit event traces to operation header."),
    r("ccsb_operationaudit", "ccsb_operationitemid", "ccsb_operationitem", "Audit event traces to operation item."),
    r("ccsb_operationaudit", "ccsb_schedulechangeid", "ccsb_schedulechange", "Audit event traces to a schedule change when applicable."),
    r("ccsb_operationaudit", "ccsb_publishsnapshotid", "ccsb_publishsnapshot", "Audit event traces to a publish snapshot when applicable."),
    r("ccsb_operationaudit", "ccsb_publishlockid", "ccsb_publishlock", "Audit event traces to a publish lock when applicable."),
    r("ccsb_operationaudit", "ccsb_actorid", "systemuser", "Dataverse actor traceability."),
    r("ccsb_schedulechange", "ccsb_boardid", "ccsb_board", "Board-level filtering and security views."),
    r("ccsb_schedulechange", "ccsb_boardversionid", "ccsb_boardversion", "Version-aware scheduling ledger."),
    r("ccsb_schedulechange", "ccsb_scheduleversionid", "ccsb_scheduleversion", "Schedule version affected by the change."),
    r("ccsb_schedulechange", "ccsb_scheduleitemid", "ccsb_scheduleitem", "Item-level mutation target."),
    r("ccsb_schedulechange", "ccsb_scheduleassignmentid", "ccsb_scheduleassignment", "Assignment-level mutation target."),
    r("ccsb_schedulechange", "ccsb_schedulerequirementid", "ccsb_schedulerequirement", "Requirement-level mutation target."),
    r("ccsb_schedulechange", "ccsb_resourceid", "ccsb_resource", "Resource-level mutation target."),
    r("ccsb_schedulechange", "ccsb_operationid", "ccsb_operation", "Command traceability."),
    r("ccsb_schedulechange", "ccsb_operationitemid", "ccsb_operationitem", "Batch item traceability."),
    r("ccsb_schedulechange", "ccsb_publishlockid", "ccsb_publishlock", "Lock checked by the change."),
    r("ccsb_schedulechange", "ccsb_requestedby", "systemuser", "Requester accountability."),
    r("ccsb_schedulechange", "ccsb_approvedby", "systemuser", "Approver accountability."),
    r("ccsb_publishsnapshotitem", "ccsb_publishsnapshotid", "ccsb_publishsnapshot", "Snapshot header owns the item.", "Yes"),
    r("ccsb_publishsnapshotitem", "ccsb_schedulechangeid", "ccsb_schedulechange", "Change-to-snapshot traceability."),
    r("ccsb_publishsnapshotitem", "ccsb_scheduleitemid", "ccsb_scheduleitem", "Captured schedule item."),
    r("ccsb_publishsnapshotitem", "ccsb_scheduleassignmentid", "ccsb_scheduleassignment", "Captured assignment."),
    r("ccsb_publishsnapshotitem", "ccsb_schedulerequirementid", "ccsb_schedulerequirement", "Captured requirement."),
    r("ccsb_publishsnapshotitem", "ccsb_resourceid", "ccsb_resource", "Captured resource."),
    r("ccsb_publishlock", "ccsb_boardid", "ccsb_board", "Board lock scope."),
    r("ccsb_publishlock", "ccsb_boardversionid", "ccsb_boardversion", "Version lock scope."),
    r("ccsb_publishlock", "ccsb_scheduleversionid", "ccsb_scheduleversion", "Schedule version lock scope."),
    r("ccsb_publishlock", "ccsb_publishsnapshotid", "ccsb_publishsnapshot", "Snapshot that created or is protected by the lock."),
    r("ccsb_publishlock", "ccsb_operationid", "ccsb_operation", "Operation that acquired the lock."),
    r("ccsb_publishlock", "ccsb_groupnodeid", "ccsb_groupnode", "Group/node lock scope."),
    r("ccsb_publishlock", "ccsb_resourceid", "ccsb_resource", "Resource lock scope."),
    r("ccsb_publishlock", "ccsb_scheduleitemid", "ccsb_scheduleitem", "Schedule item lock scope."),
    r("ccsb_publishlock", "ccsb_supersedeslockid", "ccsb_publishlock", "Lock lineage when a later lock supersedes an earlier lock."),
    r("ccsb_publishlock", "ccsb_lockedby", "systemuser", "Lock acquisition accountability."),
    r("ccsb_publishlock", "ccsb_releasedby", "systemuser", "Release accountability."),
    r("ccsb_publishlock", "ccsb_overriddenby", "systemuser", "Override accountability."),
    r("ccsb_outboxevent", "ccsb_boardid", "ccsb_board", "Board context for filtering and partitioning."),
    r("ccsb_outboxevent", "ccsb_boardversionid", "ccsb_boardversion", "Board version context."),
    r("ccsb_outboxevent", "ccsb_scheduleversionid", "ccsb_scheduleversion", "Schedule version context."),
    r("ccsb_outboxevent", "ccsb_operationid", "ccsb_operation", "Operation that emitted the event."),
    r("ccsb_outboxevent", "ccsb_schedulechangeid", "ccsb_schedulechange", "Change event source."),
    r("ccsb_outboxevent", "ccsb_publishsnapshotid", "ccsb_publishsnapshot", "Publish event source."),
    r("ccsb_outboxevent", "ccsb_publishlockid", "ccsb_publishlock", "Lock event source."),
]


CHANGES = [
    {
        "id": "CHG-001",
        "area": "Ownership",
        "change": "Use OrganizationOwned for operationaudit, schedulechange, publishlock, publishsnapshotitem, and outboxevent; use UserOwned only for resourcecapability.",
        "evidence": "Dataverse ownership is chosen at table creation and cannot be changed later; organization ownership is recommended when granular user-level control is unnecessary.",
        "reason": "Prevents audit, ledger, lock, and integration rows from losing visibility or changing behavior because a user owner, business unit, or assignment cascade changes.",
        "impact": "Breaking if previous unmanaged tables were already created as UserOwned. Recreate before data load or migrate into new tables.",
    },
    {
        "id": "CHG-002",
        "area": "Publish Lock",
        "change": "Define publishlock as a business protection lock, not a distributed worker lease.",
        "evidence": "Alternate-key guidance warns against unsafe key values and field-secured key columns; cascade guidance favors bounded explicit relationships for governance records.",
        "reason": "Lock scope, override, and release are business facts. Worker claim/heartbeat fields are transient operational state and belong on outbox or a separate lease table.",
        "impact": "Remove lock-token alternate key. Keep any worker lease need as P1 ccsb_operationlease or outbox claim fields.",
    },
    {
        "id": "CHG-003",
        "area": "Relationships",
        "change": "Reduce relationship fan-out and use Restrict delete plus NoCascade for control/evidence tables.",
        "evidence": "Dataverse Restrict prevents referenced row deletion while children exist; NoCascade avoids inherited owner/share/reparent surprises.",
        "reason": "Evidence records must remain stable and queryable. Not every cross-reference needs a physical lookup in P0; correlation ids and operation ids cover traceability.",
        "impact": "Keep direct lookups only where forms, security views, or common queries require them. Add deferred links after telemetry proves need.",
    },
    {
        "id": "CHG-004",
        "area": "Schedule Change",
        "change": "Use ccsb_changestatus and ccsb_proposedpayloadjson; add committedpayloadjson only for transformed or partial commits.",
        "evidence": "Dataverse already has platform statecode/statuscode; Project Operations schedule APIs perform scheduling mutations through API contracts and operation sets.",
        "reason": "Avoids confusing product lifecycle with platform state. Separates requested payload from actual committed payload for adapter-driven writes.",
        "impact": "Rename ccsb_changestate if introduced; update plug-ins/flows/PCF to read changestatus.",
    },
    {
        "id": "CHG-005",
        "area": "Operation Audit",
        "change": "Keep product audit concise and append-only; do not store full before/after images in operationaudit.",
        "evidence": "Dataverse audit logs platform changes and consumes log storage; CCSB needs product-specific policy, correlation, and reason evidence.",
        "reason": "Searchable audit events stay small while schedulechange/snapshotitem own the larger rollback and payload evidence.",
        "impact": "Move image-heavy audit fields to schedulechange or publishsnapshotitem. Add policyversion, diagnosticjson, and previousrecordhash as P1 or secure fields.",
    },
    {
        "id": "CHG-006",
        "area": "Outbox",
        "change": "Combine aggregate ordering and secure destination keys; never store endpoint URLs, secrets, SAS URLs, or tokens.",
        "evidence": "Column-level security controls sensitive field access, but secure columns still require careful profile management and some columns cannot be secured.",
        "reason": "Destination configuration should be resolved through secure platform configuration, not persisted in integration events.",
        "impact": "Use ccsb_destinationtype and ccsb_destinationkey. Treat payload/error/dead-letter fields as field-secured and retention-managed.",
    },
    {
        "id": "CHG-007",
        "area": "Field Mapping",
        "change": "Extend existing field mapping with ccsb_isrollbackmanaged, ccsb_issensitive, and ccsb_isdisplayonly before enforcing rollback scope.",
        "evidence": "The comparison document identified that field-scoped rollback requires managed field flags; column security guidance shows not every sensitive field can be secured by type.",
        "reason": "Rollback and UI presentation rules need explicit metadata rather than inferring from labels or payload content.",
        "impact": "Add fields to existing ccsb_fieldmapping or equivalent mapping table before enabling field-scoped publish/rollback enforcement.",
    },
    {
        "id": "CHG-008",
        "area": "Custom APIs",
        "change": "Require Custom APIs/plug-ins for publish, rollback, lock, unlock, schedule mutation, and outbox creation.",
        "evidence": "Dataverse Custom APIs can consolidate operations, invoke plug-in logic, require privileges, and should be non-customizable in managed solutions.",
        "reason": "Direct CRUD would bypass validation, concurrency, audit, snapshot, and outbox guarantees.",
        "impact": "Security roles should deny normal app users direct write privileges on control tables and expose API privileges instead.",
    },
]


def count_csv_rows(path: Path) -> int | None:
    if not path.exists():
        return None
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return max(sum(1 for _ in csv.DictReader(handle)), 0)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    return value.replace("_", "-")


def table(headers: list[str], rows: list[list[object]], cls: str = "") -> str:
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "\n".join("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows)
    klass = f' class="{cls}"' if cls else ""
    return f"<table{klass}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="badge {kind}">{esc(text)}</span>'


def field_table(entity: dict) -> str:
    rows = []
    for item in entity["fields"]:
        rows.append([
            f"<code>{esc(item['logical'])}</code>",
            esc(item["type"]),
            esc(item["required"]),
            esc(item["security"]),
            esc(item["purpose"]),
            esc(item["constraint"]),
        ])
    return table(["Logical name", "Type", "Required", "Security", "Purpose", "Constraints"], rows, "dense")


def relationship_table(rows_in: list[dict]) -> str:
    rows = []
    for item in rows_in:
        rows.append([
            f"<code>{esc(item['source'])}</code>",
            f"<code>{esc(item['lookup'])}</code>",
            f"<code>{esc(item['target'])}</code>",
            esc(item["required"]),
            esc(item["cascade"]),
            esc(item["why"]),
        ])
    return table(["Source", "Lookup", "Target", "Required", "Cascade", "Why kept in P0"], rows, "dense")


def change_table() -> str:
    rows = []
    for item in CHANGES:
        rows.append([
            f"<code>{esc(item['id'])}</code>",
            esc(item["area"]),
            esc(item["change"]),
            esc(item["evidence"]),
            esc(item["reason"]),
            esc(item["impact"]),
        ])
    return table(["ID", "Area", "Optimized change", "Evidence", "Why CCSB should do it", "Migration impact"], rows, "wide")


def write_change_csv() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUT_CHANGES.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "area", "change", "evidence", "reason", "impact"])
        writer.writeheader()
        writer.writerows(CHANGES)


def build_html() -> str:
    previous_field_count = count_csv_rows(PREVIOUS_FIELD_CSV)
    previous_rel_count = count_csv_rows(PREVIOUS_REL_CSV)
    field_count = sum(len(e["fields"]) for e in ENTITIES)
    rel_count = len(RELATIONSHIPS)
    secure_count = sum(1 for e in ENTITIES for item in e["fields"] if "security" in item["security"].lower())
    changed_owners = sum(1 for e in ENTITIES if e["ownership"] != e["previous_codex"])

    nav_items = [
        ("summary", "Decision"),
        ("evidence", "Evidence"),
        ("changes", "Changes"),
        ("schema", "Optimized Schema"),
        ("relationships", "Relationships"),
        ("validation", "Validation Rules"),
        ("migration", "Migration Plan"),
        ("appendix", "Appendix"),
    ]
    for entity in ENTITIES:
        nav_items.append((slug(entity["logical"]), entity["display"]))
    nav = "\n".join(f'<a href="#{esc(anchor)}">{esc(label)}</a>' for anchor, label in nav_items)

    metrics = [
        ("Optimized tables", "6"),
        ("Optimized P0 fields", str(field_count)),
        ("Optimized P0 relationships", str(rel_count)),
        ("Field-secured candidates", str(secure_count)),
        ("Ownership decisions changed from Codex v1.1", str(changed_owners)),
        ("Previous Codex field count", str(previous_field_count or "not found")),
        ("Previous Codex relationship count", str(previous_rel_count or "not found")),
    ]
    metric_cards = "\n".join(
        f'<div class="metric"><b>{esc(value)}</b><span>{esc(label)}</span></div>' for label, value in metrics
    )

    source_rows = [
        [
            esc("ChatGPT Plus design"),
            f"<code>{esc(PLUS_DESIGN)}</code>",
            esc("Lean product-owned schema, all six new tables organization-owned, strong canonical naming and scope control."),
        ],
        [
            esc("Hybrid comparison document"),
            f"<code>{esc(COMPARISON_DOC)}</code>",
            esc("Recommended a controlled hybrid: use Plus as structural baseline and import selected Codex fields where they close real gaps."),
        ],
        [
            esc("Previous Codex schema package"),
            f"<code>{esc(CODEX_PREVIOUS)}</code>",
            esc("Broader schema proposal with 214 fields and 67 relationships, useful for coverage but too broad for P0 implementation."),
        ],
    ]

    ms_rows = [
        [
            f'<a href="{esc(src["url"])}">{esc(src["label"])}</a>',
            esc(src["evidence"]),
            esc(src["design_use"]),
        ]
        for src in MICROSOFT_SOURCES
    ]

    ownership_rows = []
    for entity in ENTITIES:
        kind = "ok" if entity["ownership"] == entity["previous_codex"] else "warn"
        ownership_rows.append([
            f"<code>{esc(entity['logical'])}</code>",
            badge(entity["ownership"], "ok" if entity["ownership"] == "OrganizationOwned" else "info"),
            esc(entity["plus"]),
            badge(entity["previous_codex"], kind),
            esc(entity["decision"]),
        ])

    entity_cards = []
    for entity in ENTITIES:
        deferred = "".join(f"<li>{esc(item)}</li>" for item in entity["defer"])
        entity_cards.append(
            f"""
            <section class="entity" id="{esc(slug(entity["logical"]))}">
              <h3><code>{esc(entity["logical"])}</code></h3>
              <div class="entity-head">
                <span>{badge(entity["ownership"], "ok" if entity["ownership"] == "OrganizationOwned" else "info")}</span>
                <span><strong>Keys:</strong> {", ".join(f"<code>{esc(k)}</code>" for k in entity["keys"])}</span>
              </div>
              <p><strong>Decision:</strong> {esc(entity["decision"])}</p>
              <p><strong>Audit/security posture:</strong> {esc(entity["audit"])}</p>
              {field_table(entity)}
              <h4>Deferred or Rejected From P0</h4>
              <ul>{deferred}</ul>
            </section>
            """
        )

    migration_items = [
        ("MIG-001", "Stop and recreate if wrong ownership already exists", "If operationaudit, schedulechange, or publishlock were created as UserOwned, do not build on them. Ownership cannot be changed after table creation. Recreate before production data is loaded, or migrate records into new OrganizationOwned tables with canonical names."),
        ("MIG-002", "Rename before import where possible", "Use ccsb_auditeventkey, ccsb_occurredon, ccsb_changestatus, ccsb_sequence, ccsb_proposedpayloadjson, ccsb_destinationtype, and ccsb_destinationkey. Keep old names only as temporary migration aliases in integration maps, not as canonical schema."),
        ("MIG-003", "Protect alternate keys", "Alternate-key fields must be clean text or supported simple types, not field-secured, and sanitized for GET/PATCH/upsert. Do not use lock tokens, raw external URLs, or secret-bearing values in keys."),
        ("MIG-004", "Add field mapping flags first", "Before enforcing publish/rollback scope, add ccsb_isrollbackmanaged, ccsb_issensitive, and ccsb_isdisplayonly to the existing field mapping table and backfill values."),
        ("MIG-005", "Move direct writes behind APIs", "Configure security roles and command surfaces so users invoke Custom APIs. Plug-ins then create schedulechange, operationaudit, publishsnapshotitem, publishlock, and outboxevent rows in one governed flow."),
        ("MIG-006", "Phase relationships", "Deploy only the P0 lookup set in this report. Add deferred relationships when model-driven navigation, reporting, or Dataverse query telemetry proves they are needed."),
        ("MIG-007", "Secure payload and diagnostics", "Create field security profiles for payloadjson, diagnosticjson, reason, error, and dead-letter fields. Test with a non-system-admin account because system administrators bypass column security."),
        ("MIG-008", "Plan retention and archive", "Define retentionuntil values and archive jobs for audit, snapshot, lock, and outbox tables. Dataverse audit log retention is separate from CCSB product-retention fields."),
    ]
    migration_rows = [[f"<code>{esc(i)}</code>", esc(title), esc(detail)] for i, title, detail in migration_items]

    validation_rows = [
        ("VAL-001", "Logical names", "All custom tables and columns must start with ccsb_, be lower-case, and match ^ccsb_[a-z0-9]+(_[a-z0-9]+)*$ except platform columns and systemuser lookups."),
        ("VAL-002", "Ownership freeze", "Fail build/package review when a new table ownership differs from the approved ownership matrix."),
        ("VAL-003", "Alternate keys", "Fail when alternate-key columns are field-secured, too long, contain unsafe integration characters, or exceed Dataverse count/size constraints."),
        ("VAL-004", "Relationship cascade", "Fail when control/evidence relationships use Cascade delete or cascading assign/share/reparent unless an exception record exists."),
        ("VAL-005", "Sensitive fields", "Warn when payload, diagnostic, reason, error, token, or secret-like columns are not marked field-secured or intentionally excluded."),
        ("VAL-006", "No raw secret storage", "Fail when field names or sample data include url, sas, token, secret, password, connectionstring, or endpoint unless the approved purpose is a logical configuration key."),
        ("VAL-007", "State vocabulary", "Warn when custom lifecycle fields use state/statecode naming. Prefer status or explicit business terms."),
        ("VAL-008", "Dependency mapping", "Every lookup to Field Service, Project Operations, or URS concepts must be optional or adapter-owned unless the target solution is a declared dependency."),
    ]
    validation_rows = [[f"<code>{esc(i)}</code>", esc(rule), esc(test)] for i, rule, test in validation_rows]

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CCSB Optimized Database Design Evidence v1.1</title>
  <style>
    :root {{
      --ink: #17202a;
      --muted: #5f6f82;
      --line: #d7dee8;
      --panel: #f7f9fc;
      --nav: #102033;
      --accent: #116466;
      --accent2: #7c3aed;
      --warn: #9a5b00;
      --ok: #137333;
      --code: #edf2f7;
    }}
    * {{ box-sizing: border-box; }}
    html {{ scroll-behavior: smooth; }}
    body {{
      margin: 0;
      color: var(--ink);
      font: 14px/1.55 "Segoe UI", Arial, sans-serif;
      background: white;
    }}
    nav {{
      position: fixed;
      inset: 0 auto 0 0;
      width: 280px;
      padding: 24px 18px;
      background: var(--nav);
      color: white;
      overflow-y: auto;
    }}
    nav h1 {{
      margin: 0 0 10px;
      font-size: 20px;
      line-height: 1.15;
      letter-spacing: 0;
    }}
    nav p {{
      margin: 0 0 18px;
      color: #c9d7e8;
      font-size: 12px;
    }}
    nav a {{
      display: block;
      color: #e9f3ff;
      text-decoration: none;
      padding: 7px 8px;
      border-radius: 6px;
      overflow-wrap: anywhere;
    }}
    nav a:hover {{ background: rgba(255,255,255,.12); }}
    main {{
      margin-left: 280px;
      padding: 34px 42px 80px;
      max-width: 1480px;
    }}
    section {{ margin: 0 0 34px; }}
    h2 {{
      margin: 0 0 12px;
      font-size: 24px;
      letter-spacing: 0;
      border-bottom: 2px solid var(--line);
      padding-bottom: 8px;
    }}
    h3 {{ margin: 24px 0 10px; font-size: 19px; letter-spacing: 0; }}
    h4 {{ margin: 18px 0 8px; font-size: 15px; }}
    p {{ max-width: 1120px; }}
    .lede {{
      font-size: 17px;
      max-width: 1160px;
    }}
    .callout {{
      border-left: 5px solid var(--accent);
      background: var(--panel);
      padding: 14px 16px;
      margin: 14px 0 20px;
    }}
    .warnbox {{ border-left-color: var(--warn); }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin: 18px 0 24px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      background: white;
      min-height: 84px;
    }}
    .metric b {{ display: block; font-size: 26px; color: var(--accent); }}
    .metric span {{ display: block; color: var(--muted); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 12px 0 18px;
      table-layout: fixed;
    }}
    th, td {{
      border: 1px solid var(--line);
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
      overflow-wrap: anywhere;
    }}
    th {{
      background: #eaf1f8;
      color: #16283a;
      font-weight: 650;
    }}
    table.dense th, table.dense td {{ font-size: 12px; padding: 7px 8px; }}
    table.wide th:nth-child(1), table.wide td:nth-child(1) {{ width: 86px; }}
    code {{
      background: var(--code);
      border-radius: 4px;
      padding: 1px 4px;
      font-family: Consolas, "Courier New", monospace;
      font-size: .92em;
    }}
    .badge {{
      display: inline-block;
      padding: 2px 8px;
      border-radius: 999px;
      background: #e8eef5;
      color: #24384d;
      font-weight: 650;
      white-space: nowrap;
    }}
    .badge.ok {{ background: #e5f4ea; color: var(--ok); }}
    .badge.warn {{ background: #fff3dc; color: var(--warn); }}
    .badge.info {{ background: #eaf0ff; color: #254f9b; }}
    .entity {{
      border-top: 1px solid var(--line);
      padding-top: 4px;
    }}
    .entity-head {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px 18px;
      align-items: center;
      margin: 8px 0 10px;
    }}
    ul {{ margin-top: 6px; }}
    li {{ margin: 4px 0; }}
    .decision-list li {{ margin-bottom: 8px; }}
    @media (max-width: 920px) {{
      nav {{ position: static; width: auto; max-height: none; }}
      main {{ margin-left: 0; padding: 24px 18px 64px; }}
      table {{ table-layout: auto; }}
    }}
  </style>
</head>
<body>
  <nav>
    <h1>CCSB Database Optimization v1.1</h1>
    <p>Evidence-backed hybrid design generated {date.today().isoformat()}</p>
    {nav}
  </nav>
  <main>
    <section id="summary">
      <h2>Decision</h2>
      <p class="lede">Adopt a controlled hybrid design: keep the lean product boundary from the ChatGPT Plus document, apply the comparison document's corrections, and retain only the Codex fields and relationships that protect publish, rollback, audit, and integration behavior in P0.</p>
      <div class="metrics">{metric_cards}</div>
      <div class="callout warnbox">
        <strong>Most important correction:</strong> change <code>ccsb_operationaudit</code>, <code>ccsb_schedulechange</code>, and <code>ccsb_publishlock</code> from the previous Codex user-owned proposal to <strong>OrganizationOwned</strong> before table creation. Dataverse ownership cannot be changed after the table is created.
      </div>
      <ul class="decision-list">
        <li><strong>Use user/team ownership only where user-level stewardship matters:</strong> <code>ccsb_resourcecapability</code>.</li>
        <li><strong>Use organization ownership for evidence and control:</strong> audit, schedule ledger, snapshot item, publish lock, and outbox records.</li>
        <li><strong>Keep publish lock as a business lock:</strong> worker leases and delivery claims belong in outbox or a future lease table.</li>
        <li><strong>Keep audit small:</strong> audit records store product decisions, reasons, policy, outcome, and correlation; payload images stay in schedulechange/snapshotitem.</li>
        <li><strong>Use adapter alignment:</strong> map to Field Service, URS, and Project Operations concepts without hard dependencies unless a solution dependency is explicitly declared.</li>
      </ul>
    </section>

    <section id="evidence">
      <h2>Evidence Reviewed</h2>
      <h3>Project Documents</h3>
      {table(["Source", "Location", "Evidence contribution"], source_rows)}
      <h3>Microsoft/Dynamics Evidence</h3>
      {table(["Source", "Relevant evidence", "Design use"], ms_rows)}
    </section>

    <section id="changes">
      <h2>Evidence-Based Changes</h2>
      <p>The table below is the change log that should be used to update the schema design and to explain the optimization in architecture review.</p>
      {change_table()}
    </section>

    <section id="schema">
      <h2>Optimized Schema Overview</h2>
      <p>This is the recommended P0 physical model. P1 fields are named only where they solve a known future issue but should not be imported until the owning workflow is ready.</p>
      {table(["Entity", "Optimized ownership", "Plus document", "Previous Codex", "Decision"], ownership_rows)}
    </section>

    <section id="relationships">
      <h2>P0 Relationship Set</h2>
      <p>Relationship fan-out is intentionally lower than the prior broad Codex proposal. Use direct lookups for common forms, navigation, and security views; use operation, correlation, source identity, and payload hashes for deeper traceability.</p>
      {relationship_table(RELATIONSHIPS)}
    </section>

    <section id="validation">
      <h2>Logical-Name and Schema Validation</h2>
      <p>These checks should become automated package validation rules before future schema imports.</p>
      {table(["ID", "Rule", "Automated test"], validation_rows)}
    </section>

    <section id="migration">
      <h2>Migration and Continuation Plan</h2>
      <p>Implement these steps in order. The first two steps are deliberately front-loaded because changing ownership or logical names later is the highest-cost failure mode.</p>
      {table(["ID", "Step", "Action"], migration_rows)}
    </section>

    {"".join(entity_cards)}

    <section id="appendix">
      <h2>Appendix: Design Notes</h2>
      <h3>Why the hybrid is better than either input unchanged</h3>
      <p>The Plus design is appropriately lean but under-specifies runtime evidence, outbox delivery, and rollback fields that CCSB needs to operate safely. The previous Codex design covers those concerns but over-rotates into P0 breadth, especially ownership choices and relationship density. The optimized design keeps the product boundary small while preserving the fields required for governed mutation, publish evidence, retryable integration, and rollback.</p>
      <h3>Recommended versioning strategy</h3>
      <ul>
        <li><strong>Schema v1.1:</strong> create the six optimized tables with ownership, keys, security, and P0 relationships from this report.</li>
        <li><strong>Schema v1.2:</strong> add policy hash-chain fields, snapshot predecessor relationships, and capability taxonomy only after APIs and data volume justify them.</li>
        <li><strong>Schema v2.0:</strong> introduce dedicated lease or dispatch tables only if operational telemetry proves outbox claim fields are insufficient.</li>
      </ul>
      <h3>Implementation acceptance criteria</h3>
      <ul>
        <li>All six tables import with the approved ownership matrix.</li>
        <li>All alternate keys are sanitized, unique, non-field-secured, and below Dataverse key limits.</li>
        <li>All control/evidence relationships use Restrict delete and NoCascade assign/share/reparent unless exception-approved.</li>
        <li>Payload, diagnostic, reason, error, and dead-letter fields are field-security reviewed.</li>
        <li>Model-driven app users cannot directly bypass Custom APIs for publish, rollback, lock, unlock, or schedule mutation workflows.</li>
      </ul>
    </section>
  </main>
</body>
</html>
"""
    return html_doc


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_change_csv()
    OUT_HTML.write_text(build_html(), encoding="utf-8")
    print(f"Wrote {OUT_HTML}")
    print(f"Wrote {OUT_CHANGES}")


if __name__ == "__main__":
    main()
