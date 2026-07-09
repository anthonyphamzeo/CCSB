# CCSB Foundation Schema — Data Dictionary
**Solution:** `ccsb_foundationschema`  
**Version:** `1.0.0.0`  
**Ownership:** User-owned for all foundation tables.  
**Relationship delete policy:** Restrict.
## Purpose
This schema adds the product-level configuration, mapping, lifecycle, authorization, projection, validation, and operation records required by Planora/CCSB. The base 26 V1 operational tables remain in `CCSB_Core`; this solution extends them without changing or replacing their physical identities.
## Important semantic distinction
- `ccsb_boardregistry` is the stable **configuration identity**. `ccsb_scheduleboard` remains the operational schedule-board record.
- `ccsb_boardversion` is the immutable **configuration version**. `ccsb_scheduleversion` remains the operational/published schedule version.
## New tables
### Location — `ccsb_location`

Operational location, facility, service area, region, cluster, or virtual location used to scope boards, resources, services, availability, and permissions.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Location Name | Primary name | Yes | Human-readable name of the location. |
| `ccsb_locationcode` — Location Code | String | Yes | Stable human-readable or source-system code for the location. Max length: 100. |
| `ccsb_locationtype` — Location Type | Choice | Yes | Classifies how the location is used operationally. Choices: Facility, Service Area, Region, Cluster, Virtual Location, Other. |
| `ccsb_externalkey` — External Key | String | No | Stable key used to reconcile this location to an external source. Max length: 200. |
| `ccsb_timezoneid` — Time Zone ID | String | No | IANA or Windows time-zone identifier used for local schedule display and validation. Max length: 100. |
| `ccsb_addressline1` — Address Line 1 | String | No | Primary street address line. Max length: 250. |
| `ccsb_addressline2` — Address Line 2 | String | No | Secondary address line. Max length: 250. |
| `ccsb_suburb` — Suburb / City | String | No | Suburb, city, or locality. Max length: 120. |
| `ccsb_stateprovince` — State / Province | String | No | State, province, or territory. Max length: 120. |
| `ccsb_postcode` — Postcode | String | No | Postal or ZIP code. Max length: 30. |
| `ccsb_countrycode` — Country Code | String | No | ISO country code. Max length: 10. |
| `ccsb_latitude` — Latitude | Decimal | No | Latitude for travel, proximity, or mapping calculations. |
| `ccsb_longitude` — Longitude | Decimal | No | Longitude for travel, proximity, or mapping calculations. |
| `ccsb_defaultcapacity` — Default Capacity | Decimal | No | Default capacity available at this location when a service does not define an override. |
| `ccsb_effectivefrom` — Effective From | DateOnly | No | Date from which the location may be used. |
| `ccsb_effectiveto` — Effective To | DateOnly | No | Date after which the location may not be used. |
| `ccsb_sortorder` — Sort Order | Integer | No | Display order within board navigation and grouping. |
| `ccsb_isschedulingenabled` — Scheduling Enabled | Boolean | Yes | Indicates whether new scheduling activity may be allocated to this location. |
| `ccsb_notes` — Notes | Memo | No | Operational notes about the location. Max length: 100000. |

**Alternate keys**
- `ccsb_Location_LocationCode_Key`: `ccsb_locationcode`

### Board Registry — `ccsb_boardregistry`

Stable product-level board identity. A board owns its configuration lifecycle and points to one active immutable Board Version.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Board Registry Name | Primary name | Yes | Human-readable board registry name. |
| `ccsb_boardcode` — Board Code | String | Yes | Stable unique code used in integrations, URLs, and configuration references. Max length: 100. |
| `ccsb_description` — Description | Memo | No | Business purpose and operating scope of the board. Max length: 100000. |
| `ccsb_boardtype` — Board Type | Choice | Yes | Primary operational use of the board. Choices: Operational Scheduling, Dispatch, Capacity Planning, Roster Planning, Read Only. |
| `ccsb_lifecyclestate` — Lifecycle State | Choice | Yes | Business lifecycle of the board identity. Choices: Draft, Active, Suspended, Retired. |
| `ccsb_defaulttimezoneid` — Default Time Zone ID | String | No | Default IANA or Windows time-zone identifier for board rendering. Max length: 100. |
| `ccsb_defaultplanninghorizondays` — Default Planning Horizon (Days) | Integer | No | Default number of days loaded when the board opens. |
| `ccsb_maxhierarchydepth` — Maximum Hierarchy Depth | Integer | No | Maximum configured group hierarchy depth for this board. |
| `ccsb_allowadhocchanges` — Allow Ad Hoc Changes | Boolean | Yes | Allows authorised planners to create or amend schedule records outside configured templates. |
| `ccsb_allowunassignedwork` — Allow Unassigned Work | Boolean | Yes | Allows valid schedule items to remain intentionally unassigned. |
| `ccsb_externalkey` — External Key | String | No | Stable external identifier for the board. Max length: 200. |
| `ccsb_effectivefrom` — Effective From | DateOnly | No | Date from which the board may be used. |
| `ccsb_effectiveto` — Effective To | DateOnly | No | Date after which the board may not be used. |

**Alternate keys**
- `ccsb_Board_BoardCode_Key`: `ccsb_boardcode`

### Board Version — `ccsb_boardversion`

Immutable, versioned configuration baseline governing mappings, views, rules, groups, status models, role definitions, and permission policies for a Board.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Board Version Name | Primary name | Yes | Human-readable version name. |
| `ccsb_versionnumber` — Version Number | Integer | Yes | Monotonically increasing version number within the Board. |
| `ccsb_versionlabel` — Version Label | String | No | Readable release label, for example 2026.1 or Winter Release. Max length: 100. |
| `ccsb_lifecyclestate` — Lifecycle State | Choice | Yes | Lifecycle of the immutable board configuration version. Choices: Draft, Validating, Ready, Active, Superseded, Retired. |
| `ccsb_validationstatus` — Validation Status | Choice | Yes | Latest validation outcome for the version. Choices: Not Run, Passed, Passed With Warnings, Failed. |
| `ccsb_effectivefrom` — Effective From | DateAndTime | No | Timestamp from which the version is permitted to be active. |
| `ccsb_effectiveto` — Effective To | DateAndTime | No | Timestamp after which the version must not be active. |
| `ccsb_activatedon` — Activated On | DateAndTime | No | Timestamp at which the version became active. |
| `ccsb_configurationhash` — Configuration Hash | String | No | Deterministic hash of normalized configuration content used to identify drift. Max length: 128. |
| `ccsb_isimmutable` — Is Immutable | Boolean | Yes | Marks the version as immutable after activation or publication. |
| `ccsb_changecomment` — Change Comment | Memo | No | Reason and summary for this version. Max length: 100000. |
| `ccsb_validationrunon` — Validation Run On | DateAndTime | No | Timestamp of the most recent validation run. |
| `ccsb_externalkey` — External Key | String | No | Stable external identifier for the board version. Max length: 200. |

### Entity Definition — `ccsb_entitydefinition`

Approved definition of a native or customer-owned Dataverse table that participates in a Board Version.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Entity Definition Name | Primary name | Yes | Readable definition name. |
| `ccsb_entitylogicalname` — Entity Logical Name | String | Yes | Dataverse logical name of the mapped source table. Max length: 128. |
| `ccsb_entitysetname` — Entity Set Name | String | No | Dataverse Web API entity-set name. Max length: 128. |
| `ccsb_entityrole` — Entity Role | Choice | Yes | Semantic scheduling role fulfilled by the source table. Choices: Booking, Activity, Assignment, Resource, Service, Customer, Availability, Shift, Leave, Location, Other. |
| `ccsb_sourcetype` — Source Type | Choice | Yes | Whether the table is native CCSB or customer-owned. Choices: Native CCSB, Customer Owned, External Virtual. |
| `ccsb_primaryidfield` — Primary ID Field | String | Yes | Logical name of the source primary ID field. Max length: 128. |
| `ccsb_primarynamefield` — Primary Name Field | String | No | Logical name of the primary display name field. Max length: 128. |
| `ccsb_defaultsort` — Default Sort | String | No | Safe default sort expression for runtime retrieval. Max length: 500. |
| `ccsb_filterodata` — OData Filter | Memo | No | Approved OData filter applied when this entity is queried by the board. Max length: 100000. |
| `ccsb_filterfetchxml` — FetchXML Filter | Memo | No | Approved FetchXML filter applied where OData is not sufficient. Max length: 100000. |
| `ccsb_allowread` — Allow Read | Boolean | Yes | Permits the runtime to read records from the mapped source. |
| `ccsb_allowcreate` — Allow Create | Boolean | Yes | Permits the runtime to create records in the mapped source. |
| `ccsb_allowupdate` — Allow Update | Boolean | Yes | Permits the runtime to update approved mapped fields. |
| `ccsb_allowdelete` — Allow Delete | Boolean | Yes | Permits the runtime to delete records in the mapped source. |
| `ccsb_allowdirectformopen` — Allow Direct Form Open | Boolean | Yes | Allows the runtime to open the mapped Dataverse form for a record. |
| `ccsb_metadataetag` — Metadata ETag | String | No | Metadata fingerprint used to detect source schema drift. Max length: 200. |
| `ccsb_lastvalidatedon` — Last Validated On | DateAndTime | No | Timestamp at which source metadata was last validated. |
| `ccsb_validationstatus` — Validation Status | Choice | Yes | Current metadata validation outcome. Choices: Unknown, Valid, Warning, Invalid. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether this entity definition is active for its Board Version. |

### Field Mapping — `ccsb_fieldmapping`

Maps an approved source field to a CCSB scheduling semantic and defines controlled transformation and write behavior.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Field Mapping Name | Primary name | Yes | Readable mapping name. |
| `ccsb_semanticname` — Semantic Name | String | Yes | Stable CCSB semantic, for example activity.start or assignment.resource. Max length: 200. |
| `ccsb_sourcefieldlogicalname` — Source Field Logical Name | String | Yes | Logical name of the mapped source field. Max length: 128. |
| `ccsb_sourcefieldtype` — Source Field Type | String | No | Dataverse metadata type of the mapped source field. Max length: 100. |
| `ccsb_targetdatatype` — Target Data Type | Choice | Yes | Expected semantic data type after transformation. Choices: String, Integer, Decimal, Boolean, Date Only, Date and Time, Lookup, Choice, JSON. |
| `ccsb_transformationtype` — Transformation Type | Choice | Yes | Transformation applied before a value is consumed or written. Choices: Direct, Lookup ID, Option Mapping, Date Time Conversion, Expression, Constant, Concatenate, JSON Path. |
| `ccsb_transformationdefinition` — Transformation Definition | Memo | No | Controlled expression or JSON definition of the transformation. Max length: 100000. |
| `ccsb_optionmapjson` — Option Map JSON | Memo | No | Explicit mapping of source choice values to CCSB semantic values. Max length: 100000. |
| `ccsb_fallbackvalue` — Fallback Value | String | No | Value used when the source value is blank or unavailable. Max length: 1000. |
| `ccsb_lookuptargetlogicalname` — Lookup Target Logical Name | String | No | Expected target table when the source field is a lookup. Max length: 128. |
| `ccsb_lookupprimarynamefield` — Lookup Primary Name Field | String | No | Display field used when resolving a lookup. Max length: 128. |
| `ccsb_isrequired` — Required | Boolean | Yes | Requires the mapping to resolve successfully before activation. |
| `ccsb_isnullable` — Nullable | Boolean | Yes | Allows the semantic value to be null. |
| `ccsb_readenabled` — Read Enabled | Boolean | Yes | Allows this mapping to be used in runtime reads. |
| `ccsb_writebehavior` — Write Behavior | Choice | Yes | Permitted runtime write behavior for this mapping. Choices: Never, Create Only, Update Allowed. |
| `ccsb_validationexpression` — Validation Expression | String | No | Optional validation expression or regular expression. Max length: 2000. |
| `ccsb_sortorder` — Sort Order | Integer | No | Evaluation order where fields depend on other mappings. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the field mapping is active. |

### Relationship Mapping — `ccsb_relationshipmapping`

Maps approved Dataverse relationships to CCSB scheduling graph semantics.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Relationship Mapping Name | Primary name | Yes | Readable relationship mapping name. |
| `ccsb_relationshiprole` — Relationship Role | String | Yes | Stable semantic such as booking.activity or activity.assignment. Max length: 200. |
| `ccsb_relationshiplogicalname` — Relationship Logical Name | String | Yes | Dataverse relationship schema/logical name. Max length: 200. |
| `ccsb_relationshiptype` — Relationship Type | Choice | Yes | Cardinality of the source relationship. Choices: Many-to-One, One-to-Many, Many-to-Many. |
| `ccsb_sourcelookupfield` — Source Lookup Field | String | No | Source lookup field used to resolve the relationship. Max length: 128. |
| `ccsb_sourcenavigationproperty` — Source Navigation Property | String | No | Web API navigation property from the source record. Max length: 200. |
| `ccsb_targetnavigationproperty` — Target Navigation Property | String | No | Web API navigation or collection property from the target record. Max length: 200. |
| `ccsb_relatedprimaryidfield` — Related Primary ID Field | String | No | Primary identifier field of the related source table. Max length: 128. |
| `ccsb_isrequired` — Required | Boolean | Yes | Requires the relationship to resolve before activation. |
| `ccsb_writebehavior` — Write Behavior | Choice | Yes | Permitted runtime write behavior for this relationship. Choices: Never, Create Only, Update Allowed. |
| `ccsb_deletebehavior` — Delete Behavior | Choice | Yes | Intended business delete policy. Physical lookup relationships are created as Restrict. Choices: Restrict, Retain Historical Reference. |
| `ccsb_filterdefinition` — Filter Definition | Memo | No | Optional condition limiting related records used by the runtime. Max length: 100000. |
| `ccsb_sortorder` — Sort Order | Integer | No | Evaluation order. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the relationship mapping is active. |

### Status Model — `ccsb_statusmodel`

Reusable lifecycle model governing allowed status states, transitions, display colors, and runtime status-write policy.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Status Model Name | Primary name | Yes | Readable status model name. |
| `ccsb_statusmodelcode` — Status Model Code | String | Yes | Stable code for the status model. Max length: 100. |
| `ccsb_appliestorole` — Applies To Role | Choice | Yes | Scheduling semantic governed by this status model. Choices: Booking, Activity, Assignment, Schedule Item, Service. |
| `ccsb_systemofrecord` — System of Record | Choice | Yes | System permitted to own the lifecycle status. Choices: Customer Source, Native CCSB, External Integration. |
| `ccsb_initialstatuscode` — Initial Status Code | String | No | Initial status key used when a record is created. Max length: 100. |
| `ccsb_terminalstatuscodesjson` — Terminal Status Codes JSON | Memo | No | JSON array of terminal status keys. Max length: 100000. |
| `ccsb_statuspalettejson` — Status Palette JSON | Memo | No | JSON color and display configuration for statuses. Max length: 100000. |
| `ccsb_allowexternalstatusupdate` — Allow External Status Update | Boolean | Yes | Allows mapped external records to update status through approved mappings. |
| `ccsb_allowmanualoverride` — Allow Manual Override | Boolean | Yes | Allows authorised users to override transition validation. |
| `ccsb_validationmode` — Validation Mode | Choice | Yes | How invalid transitions are handled. Choices: Block, Warn, Allow. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the status model is active. |
| `ccsb_sortorder` — Sort Order | Integer | No | Display and evaluation order. |

**Alternate keys**
- `ccsb_StatusModel_Code_Key`: `ccsb_statusmodelcode`

### Resource Role — `ccsb_resourcerole`

Configuration-driven named resource role used by activity requirements and assignments, including quantity and capacity rules for group bookings.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Resource Role Name | Primary name | Yes | Readable resource role name. |
| `ccsb_rolecode` — Role Code | String | Yes | Stable resource role code. Max length: 100. |
| `ccsb_description` — Description | Memo | No | Business definition and usage notes. Max length: 100000. |
| `ccsb_rolecategory` — Role Category | Choice | Yes | High-level category of resource role. Choices: Person, Vehicle, Equipment, Facility, Seat / Capacity, Other. |
| `ccsb_defaultquantity` — Default Quantity | Integer | Yes | Default number of equivalent resources required. |
| `ccsb_minimumquantity` — Minimum Quantity | Integer | Yes | Minimum number of resources required to satisfy the role. |
| `ccsb_maximumquantity` — Maximum Quantity | Integer | No | Maximum number of resources permitted for the role. |
| `ccsb_defaultcapacityrequired` — Default Capacity Required | Decimal | No | Default required capacity contribution for this role. |
| `ccsb_capacityunit` — Capacity Unit | String | No | Unit for capacity values, for example seats, hours, or kilograms. Max length: 100. |
| `ccsb_compatibleresourcefilterjson` — Compatible Resource Filter JSON | Memo | No | Approved configuration filter identifying compatible resources. Max length: 100000. |
| `ccsb_requiredskillcriteriajson` — Required Skill Criteria JSON | Memo | No | Configured skill, qualification, or certification requirements. Max length: 100000. |
| `ccsb_allowmultipleresources` — Allow Multiple Resources | Boolean | Yes | Allows multiple equivalent resources to satisfy the role. |
| `ccsb_allowsubstitution` — Allow Substitution | Boolean | Yes | Allows a compatible resource to substitute for a preferred type. |
| `ccsb_allowconcurrentassignment` — Allow Concurrent Assignment | Boolean | Yes | Allows this role to be assigned concurrently where other rules permit it. |
| `ccsb_displaycolor` — Display Color | String | No | Hex color used for role display where configured. Max length: 20. |
| `ccsb_sortorder` — Sort Order | Integer | No | Display order. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the resource role is active. |

**Alternate keys**
- `ccsb_ResourceRole_Code_Key`: `ccsb_rolecode`

### Permission Profile — `ccsb_permissionprofile`

Product-level schedule board permission policy. Dataverse security roles remain the enforcement mechanism; this profile expresses authorised board actions and scoped access.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Permission Profile Name | Primary name | Yes | Readable permission profile name. |
| `ccsb_profilecode` — Profile Code | String | Yes | Stable permission-profile code. Max length: 100. |
| `ccsb_description` — Description | Memo | No | Purpose and authorised operational scope. Max length: 100000. |
| `ccsb_profiletype` — Profile Type | Choice | Yes | Intended operational persona. Choices: Planner, Dispatcher, Resource Manager, Release Manager, Configuration Administrator, Read Only, Support. |
| `ccsb_scopemode` — Scope Mode | Choice | Yes | Scope used when evaluating permission assignments. Choices: All Boards, Board, Location, Group, Assigned Work. |
| `ccsb_canviewschedule` — Can View Schedule | Boolean | Yes | Allows viewing board data in scope. |
| `ccsb_cancreateschedule` — Can Create Schedule | Boolean | Yes | Allows creating schedule records in scope. |
| `ccsb_caneditschedule` — Can Edit Schedule | Boolean | Yes | Allows editing schedule records in scope. |
| `ccsb_canassignresources` — Can Assign Resources | Boolean | Yes | Allows assigning or unassigning resources. |
| `ccsb_canoverrideconflicts` — Can Override Conflicts | Boolean | Yes | Allows an authorised override of warnings or conflicts. |
| `ccsb_canpublish` — Can Publish | Boolean | Yes | Allows publishing approved schedule versions. |
| `ccsb_canrollback` — Can Roll Back | Boolean | Yes | Allows rollback of a publish operation where lifecycle policy permits it. |
| `ccsb_canmanageconfiguration` — Can Manage Configuration | Boolean | Yes | Allows draft configuration changes. |
| `ccsb_canviewaudit` — Can View Audit | Boolean | Yes | Allows viewing immutable snapshots and operation evidence. |
| `ccsb_canmanageintegrations` — Can Manage Integrations | Boolean | Yes | Allows controlled support actions for integration operations. |
| `ccsb_dataverserolename` — Dataverse Role Name | String | No | Optional supporting Dataverse security-role name used by deployment validation. Max length: 200. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the permission profile is active. |

**Alternate keys**
- `ccsb_PermissionProfile_Code_Key`: `ccsb_profilecode`

### Permission Assignment — `ccsb_permissionassignment`

Binds a Permission Profile to a Dataverse principal and optional board, location, or group scope.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Permission Assignment Name | Primary name | Yes | Readable permission assignment name. |
| `ccsb_principaltype` — Principal Type | Choice | Yes | Type of Dataverse or directory principal receiving the profile. Choices: System User, Team, Business Unit, Entra Group. |
| `ccsb_principalid` — Principal ID | String | Yes | Dataverse or directory principal identifier stored as a string for polymorphic portability. Max length: 100. |
| `ccsb_principaldisplayname` — Principal Display Name | String | No | Friendly principal name captured for administration and audit. Max length: 300. |
| `ccsb_accesseffect` — Access Effect | Choice | Yes | Whether the assignment grants or explicitly denies the profile. Choices: Grant, Deny. |
| `ccsb_scopetype` — Scope Type | Choice | Yes | Scope to which the permission assignment applies. Choices: All Boards, Board, Location, Group Node, Assigned Work. |
| `ccsb_scopereferenceid` — Scope Reference ID | String | No | Polymorphic scope record identifier stored as text. Max length: 100. |
| `ccsb_scopedisplayname` — Scope Display Name | String | No | Friendly scope name retained for administration and audit. Max length: 300. |
| `ccsb_effectivefrom` — Effective From | DateAndTime | No | Timestamp from which the assignment is effective. |
| `ccsb_effectiveto` — Effective To | DateAndTime | No | Timestamp after which the assignment is no longer effective. |
| `ccsb_approvalreference` — Approval Reference | String | No | Optional approval ticket or change reference. Max length: 200. |
| `ccsb_isenabled` — Enabled | Boolean | Yes | Indicates whether the assignment is active. |

### Runtime Projection — `ccsb_runtimeprojection`

Read-only materialized runtime projection of approved normalized CCSB configuration. It is never the configuration source of truth.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Runtime Projection Name | Primary name | Yes | Readable projection name. |
| `ccsb_projectiontype` — Projection Type | Choice | Yes | Kind of runtime projection. Choices: Board Configuration, Mapping Manifest, Resource Hierarchy, Runtime Payload, Permission Scope, Validation Summary. |
| `ccsb_scopetype` — Scope Type | Choice | Yes | Scope represented by the projection. Choices: Board, Location, Group, User, Global. |
| `ccsb_scopekey` — Scope Key | String | Yes | Stable scope key used to retrieve the projection. Max length: 300. |
| `ccsb_payloadjson` — Payload JSON | Memo | Yes | Read-only serialized projection payload. Max length: 1000000. |
| `ccsb_iscompressed` — Is Compressed | Boolean | Yes | Indicates whether the payload is compressed or encoded. |
| `ccsb_contenthash` — Content Hash | String | Yes | Hash of the projection payload. Max length: 128. |
| `ccsb_projectionschemaversion` — Projection Schema Version | String | Yes | Version of the runtime projection contract. Max length: 100. |
| `ccsb_sourcechangetoken` — Source Change Token | String | No | Source configuration change token used for staleness detection. Max length: 300. |
| `ccsb_generatedon` — Generated On | DateAndTime | Yes | Timestamp at which the projection was generated. |
| `ccsb_expireson` — Expires On | DateAndTime | No | Optional projection expiry timestamp. |
| `ccsb_projectionstatus` — Projection Status | Choice | Yes | Current usability of the projection. Choices: Valid, Stale, Generating, Failed, Expired. |
| `ccsb_errordetail` — Error Detail | Memo | No | Technical error detail when projection creation fails. Max length: 100000. |
| `ccsb_recordcount` — Record Count | Integer | No | Number of logical records represented by the projection. |
| `ccsb_payloadsizebytes` — Payload Size (Bytes) | Integer | No | Size of the serialized payload. |
| `ccsb_iscurrent` — Is Current | Boolean | Yes | Indicates whether this is the current projection for its type and scope. |

### Configuration Validation Result — `ccsb_configurationvalidationresult`

Evidence record produced by validation of a Board Version, mapping, policy, or runtime projection.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Validation Result Name | Primary name | Yes | Readable validation result name. |
| `ccsb_validationrunid` — Validation Run ID | String | Yes | Correlation identifier shared by validation results produced in one run. Max length: 100. |
| `ccsb_validationcode` — Validation Code | String | Yes | Stable validation rule code. Max length: 200. |
| `ccsb_validationcategory` — Validation Category | Choice | Yes | Category of validation performed. Choices: Schema, Mapping, Relationship, Status, Permission, Runtime Projection, Lifecycle, Data Quality. |
| `ccsb_severity` — Severity | Choice | Yes | Severity of the validation outcome. Choices: Information, Warning, Error, Blocking. |
| `ccsb_resultstatus` — Result Status | Choice | Yes | Current handling state of the validation result. Choices: Open, Accepted, Resolved, Suppressed. |
| `ccsb_affectedentitylogicalname` — Affected Entity Logical Name | String | No | Logical name of the affected entity. Max length: 128. |
| `ccsb_affectedrecordid` — Affected Record ID | String | No | Affected record identifier stored as text. Max length: 100. |
| `ccsb_affectedfieldlogicalname` — Affected Field Logical Name | String | No | Logical name of the affected field. Max length: 128. |
| `ccsb_message` — Message | String | Yes | Short validation message for end users and administrators. Max length: 4000. |
| `ccsb_detailjson` — Detail JSON | Memo | No | Machine-readable evidence and detailed diagnostic content. Max length: 100000. |
| `ccsb_recommendedaction` — Recommended Action | Memo | No | Suggested corrective action. Max length: 100000. |
| `ccsb_detectedon` — Detected On | DateAndTime | Yes | Timestamp at which the issue was detected. |
| `ccsb_resolvedon` — Resolved On | DateAndTime | No | Timestamp at which the issue was resolved or accepted. |
| `ccsb_resolutionnote` — Resolution Note | Memo | No | Reason for resolution, acceptance, or suppression. Max length: 100000. |
| `ccsb_externalerrorcode` — External Error Code | String | No | Source-system or technical error code where applicable. Max length: 300. |

### Operation — `ccsb_operation`

Auditable asynchronous or synchronous product operation, including validation, projection generation, publish, rollback, import, and controlled lifecycle actions.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Operation Name | Primary name | Yes | Readable operation name. |
| `ccsb_operationtype` — Operation Type | Choice | Yes | Type of operation executed by the product. Choices: Validate Board Version, Generate Projection, Publish Schedule, Rollback Schedule, Lock Scope, Unlock Scope, Import Configuration, Clone Board Version, Rebuild Cache, Reconcile Integration. |
| `ccsb_operationstatus` — Operation Status | Choice | Yes | Current execution status. Choices: Queued, In Progress, Succeeded, Succeeded With Warnings, Failed, Cancelled. |
| `ccsb_correlationid` — Correlation ID | String | Yes | End-to-end correlation identifier for telemetry and support. Max length: 100. |
| `ccsb_idempotencykey` — Idempotency Key | String | No | Stable request key preventing duplicate operation processing. Max length: 300. |
| `ccsb_targetscopetype` — Target Scope Type | Choice | Yes | Scope acted on by the operation. Choices: Board, Board Version, Schedule Board, Schedule Version, Location, Group, Configuration Package. |
| `ccsb_targetscopereferenceid` — Target Scope Reference ID | String | No | Polymorphic target identifier stored as text. Max length: 100. |
| `ccsb_requestedon` — Requested On | DateAndTime | Yes | Timestamp at which the operation was requested. |
| `ccsb_startedon` — Started On | DateAndTime | No | Timestamp at which processing began. |
| `ccsb_completedon` — Completed On | DateAndTime | No | Timestamp at which processing ended. |
| `ccsb_requestedpayloadjson` — Requested Payload JSON | Memo | No | Validated input payload supplied to the operation. Max length: 1000000. |
| `ccsb_resultjson` — Result JSON | Memo | No | Result or summary payload produced by the operation. Max length: 1000000. |
| `ccsb_errorsummary` — Error Summary | String | No | Short error summary for user-facing operation diagnostics. Max length: 4000. |
| `ccsb_errordetail` — Error Detail | Memo | No | Detailed technical error evidence. Max length: 100000. |
| `ccsb_attemptcount` — Attempt Count | Integer | Yes | Number of processing attempts. |
| `ccsb_retryafter` — Retry After | DateAndTime | No | Earliest timestamp at which a retry may be attempted. |
| `ccsb_totalitemcount` — Total Item Count | Integer | No | Total operation items expected. |
| `ccsb_succeededitemcount` — Succeeded Item Count | Integer | No | Operation items successfully processed. |
| `ccsb_faileditemcount` — Failed Item Count | Integer | No | Operation items that failed. |
| `ccsb_progresspercentage` — Progress Percentage | Integer | No | Reported progress from 0 to 100. |
| `ccsb_iscancellable` — Is Cancellable | Boolean | Yes | Indicates whether the operation may be cancelled safely. |
| `ccsb_retentionuntil` — Retention Until | DateAndTime | No | Date after which operational evidence may be archived according to policy. |

**Alternate keys**
- `ccsb_Operation_CorrelationId_Key`: `ccsb_correlationid`

### Operation Item — `ccsb_operationitem`

Child-level processing and audit evidence for one item handled by a CCSB Operation.

| Field | Type | Required | Description |
|---|---:|:---:|---|
| `ccsb_name` — Operation Item Name | Primary name | Yes | Readable operation item name. |
| `ccsb_sequencenumber` — Sequence Number | Integer | Yes | Deterministic sequence within the parent operation. |
| `ccsb_itemkey` — Item Key | String | Yes | Stable per-operation item key. Max length: 300. |
| `ccsb_itemtype` — Item Type | Choice | Yes | Type of item processed. Choices: Configuration, Schedule Item, Schedule Assignment, Schedule Requirement, Publish Snapshot, Runtime Projection, Integration Message. |
| `ccsb_actiontype` — Action Type | Choice | Yes | Action attempted for the operation item. Choices: Validate, Create, Update, Delete, Publish, Rollback, Project, Reconcile. |
| `ccsb_itemstatus` — Item Status | Choice | Yes | Current result for the operation item. Choices: Queued, In Progress, Succeeded, Warning, Failed, Skipped, Cancelled. |
| `ccsb_sourceentitylogicalname` — Source Entity Logical Name | String | No | Logical name of the source record. Max length: 128. |
| `ccsb_sourcerecordid` — Source Record ID | String | No | Source record identifier stored as text. Max length: 100. |
| `ccsb_targetentitylogicalname` — Target Entity Logical Name | String | No | Logical name of the target record. Max length: 128. |
| `ccsb_targetrecordid` — Target Record ID | String | No | Target record identifier stored as text. Max length: 100. |
| `ccsb_requestpayloadjson` — Request Payload JSON | Memo | No | Item-level input payload. Max length: 1000000. |
| `ccsb_resultpayloadjson` — Result Payload JSON | Memo | No | Item-level result payload. Max length: 1000000. |
| `ccsb_errorcode` — Error Code | String | No | Technical or business error code. Max length: 300. |
| `ccsb_errormessage` — Error Message | String | No | Short item-level error message. Max length: 4000. |
| `ccsb_errordetail` — Error Detail | Memo | No | Detailed technical error content. Max length: 100000. |
| `ccsb_processedon` — Processed On | DateAndTime | No | Timestamp at which this item was last processed. |
| `ccsb_retrycount` — Retry Count | Integer | Yes | Number of retries attempted for this item. |
| `ccsb_isretryable` — Is Retryable | Boolean | Yes | Indicates whether this item is safe to retry. |
| `ccsb_durationmilliseconds` — Duration (Milliseconds) | Integer | No | Processing duration for the item. |
| `ccsb_correlationid` — Correlation ID | String | No | End-to-end correlation identifier. Max length: 100. |

## Existing V1 table extensions
### `ccsb_resource`

- `ccsb_externalresourcekey` — **External Resource Key** (String): Stable external identifier for resource reconciliation.
- `ccsb_effectivefrom` — **Effective From** (DateOnly): Date from which the resource is eligible for the board.
- `ccsb_effectiveto` — **Effective To** (DateOnly): Date after which the resource is not eligible for the board.
### `ccsb_service`

- `ccsb_externalservicekey` — **External Service Key** (String): Stable external identifier for service reconciliation.
- `ccsb_requireslocation` — **Requires Location** (Boolean): Indicates whether a location must be resolved before scheduling.
### `ccsb_scheduleboard`

- `ccsb_operationaltimezoneid` — **Operational Time Zone ID** (String): Operational time zone used for schedule calculations and display.
- `ccsb_isruntimeenabled` — **Runtime Enabled** (Boolean): Controls whether this board may load and accept scheduling operations.
### `ccsb_scheduleitem`

- `ccsb_externalscheduleitemkey` — **External Schedule Item Key** (String): Stable external identifier for schedule-item reconciliation.

## Lookup relationships

All lookup relationships are optional at metadata level and use **Restrict** on delete. This protects schedule history and permits staged data migration. Activation/publish validation enforces any business-required relationship.

| Referencing table | Lookup | Target table |
|---|---|---|
| `ccsb_location` | `ccsb_parentlocationid` — Parent Location | `ccsb_location` |
| `ccsb_location` | `ccsb_defaultcalendarid` — Default Calendar | `ccsb_calendar` |
| `ccsb_boardregistry` | `ccsb_defaultlocationid` — Default Location | `ccsb_location` |
| `ccsb_boardregistry` | `ccsb_defaultcalendarid` — Default Calendar | `ccsb_calendar` |
| `ccsb_boardregistry` | `ccsb_defaultviewid` — Default View | `ccsb_viewdefinition` |
| `ccsb_boardversion` | `ccsb_boardid` — Board | `ccsb_boardregistry` |
| `ccsb_boardregistry` | `ccsb_activeboardversionid` — Active Board Version | `ccsb_boardversion` |
| `ccsb_boardversion` | `ccsb_supersedesboardversionid` — Supersedes Board Version | `ccsb_boardversion` |
| `ccsb_boardversion` | `ccsb_clonedfromboardversionid` — Cloned From Board Version | `ccsb_boardversion` |
| `ccsb_entitydefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_fieldmapping` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_fieldmapping` | `ccsb_entitydefinitionid` — Entity Definition | `ccsb_entitydefinition` |
| `ccsb_relationshipmapping` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_relationshipmapping` | `ccsb_sourceentitydefinitionid` — Source Entity Definition | `ccsb_entitydefinition` |
| `ccsb_relationshipmapping` | `ccsb_relatedentitydefinitionid` — Related Entity Definition | `ccsb_entitydefinition` |
| `ccsb_statusmodel` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_statusmodel` | `ccsb_sourceentitydefinitionid` — Source Entity Definition | `ccsb_entitydefinition` |
| `ccsb_statusmodel` | `ccsb_statusfieldmappingid` — Status Field Mapping | `ccsb_fieldmapping` |
| `ccsb_resourcerole` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_permissionprofile` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_permissionassignment` | `ccsb_permissionprofileid` — Permission Profile | `ccsb_permissionprofile` |
| `ccsb_permissionassignment` | `ccsb_boardid` — Board | `ccsb_boardregistry` |
| `ccsb_permissionassignment` | `ccsb_locationid` — Location | `ccsb_location` |
| `ccsb_permissionassignment` | `ccsb_groupnodeid` — Group Node | `ccsb_groupnode` |
| `ccsb_runtimeprojection` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_configurationvalidationresult` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_configurationvalidationresult` | `ccsb_operationid` — Operation | `ccsb_operation` |
| `ccsb_operation` | `ccsb_boardid` — Board | `ccsb_boardregistry` |
| `ccsb_operation` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_operationitem` | `ccsb_operationid` — Operation | `ccsb_operation` |
| `ccsb_operationitem` | `ccsb_configurationvalidationresultid` — Configuration Validation Result | `ccsb_configurationvalidationresult` |
| `ccsb_resource` | `ccsb_primarylocationid` — Primary Location | `ccsb_location` |
| `ccsb_resource` | `ccsb_defaultresourceroleid` — Default Resource Role | `ccsb_resourcerole` |
| `ccsb_service` | `ccsb_defaultlocationid` — Default Location | `ccsb_location` |
| `ccsb_scheduleboard` | `ccsb_boardregistryid` — Board Registry | `ccsb_boardregistry` |
| `ccsb_scheduleboard` | `ccsb_activeboardversionid` — Active Board Version | `ccsb_boardversion` |
| `ccsb_scheduleversion` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_scheduleversion` | `ccsb_publishoperationid` — Publish Operation | `ccsb_operation` |
| `ccsb_boardconfiguration` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_eventtypedefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_resourcedefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_groupdefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_viewdefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_ruledefinition` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_statusdefinition` | `ccsb_statusmodelid` — Status Model | `ccsb_statusmodel` |
| `ccsb_statustransition` | `ccsb_statusmodelid` — Status Model | `ccsb_statusmodel` |
| `ccsb_schedulerequirement` | `ccsb_resourceroleid` — Resource Role | `ccsb_resourcerole` |
| `ccsb_scheduleassignment` | `ccsb_resourceroleid` — Resource Role | `ccsb_resourcerole` |
| `ccsb_scheduleitem` | `ccsb_locationid` — Location | `ccsb_location` |
| `ccsb_scheduleitem` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_publishsnapshot` | `ccsb_boardversionid` — Board Version | `ccsb_boardversion` |
| `ccsb_publishsnapshot` | `ccsb_operationid` — Operation | `ccsb_operation` |

## Counts

- New foundation tables: **14**
- New-table business fields including primary name: **228**
- New lookup relationships: **52**
- Existing V1 extension fields: **8**
- Total columns/relationships provisioned: **288**
