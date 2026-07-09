# CCSB Core — Table Ownership Register

## Decision

This base solution creates **26 tables**. Ownership is selected now because Dataverse does not allow a custom table's ownership model to be changed after creation.

| Ownership type | Table count | Design purpose |
|---|---:|---|
| Organization-owned | 17 | Product definitions, shared reference/structure data, and immutable version or snapshot records |
| User/team-owned | 9 | Operational scheduling records where owner/team access may become useful |

No table is created as an Activity table. No table includes Notes, Activities, data rows, business fields, lookups, Choices, forms, views, or app navigation in this base release.

## Organization-owned tables

| Logical name | Display name | Category | Primary name label | Rationale |
|---|---|---|---|---|
| `ccsb_board` | Schedule Board | Configuration | Schedule Board Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_boardconfiguration` | Board Configuration | Configuration | Board Configuration Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_viewdefinition` | View Definition | Configuration | View Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_resourcedefinition` | Resource Definition | Configuration | Resource Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_eventtypedefinition` | Event Type Definition | Configuration | Event Type Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_groupdefinition` | Group Definition | Configuration | Group Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_statusdefinition` | Status Definition | Configuration | Status Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_statustransition` | Status Transition | Configuration | Status Transition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_ruledefinition` | Rule Definition | Configuration | Rule Definition Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_calendar` | Calendar | Operational | Calendar Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_calendarrule` | Calendar Rule | Operational | Calendar Rule Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_calendarexception` | Calendar Exception | Operational | Calendar Exception Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_publicholiday` | Public Holiday | Operational | Public Holiday Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_groupnode` | Group Node | Operational | Group Node Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_groupmembership` | Group Membership | Operational | Group Membership Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_scheduleversion` | Schedule Version | Schedule graph | Schedule Version Name | Shared reusable product configuration or governed reference/snapshot data. |
| `ccsb_publishsnapshot` | Publish Snapshot | Schedule graph | Publish Snapshot Name | Shared reusable product configuration or governed reference/snapshot data. |

## User/team-owned tables

| Logical name | Display name | Category | Primary name label | Rationale |
|---|---|---|---|---|
| `ccsb_resource` | Resource | Operational | Resource Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_service` | Service | Operational | Service Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_shift` | Shift | Operational | Shift Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_availabilitywindow` | Availability Window | Operational | Availability Window Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_leave` | Leave | Operational | Leave Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_scheduleitem` | Schedule Item | Schedule graph | Schedule Item Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_schedulerequirement` | Schedule Requirement | Schedule graph | Schedule Requirement Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_scheduleassignment` | Schedule Assignment | Schedule graph | Schedule Assignment Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |
| `ccsb_conflict` | Scheduling Conflict | Schedule graph | Scheduling Conflict Name | Operational record; user/team ownership preserves future scope for dispatcher or team-based access. |

## Implementation notes

1. **`ccsb_resource` is user/team-owned** deliberately. A later security model can permit ownership by a team, region, or operating unit without changing table type.
2. **`ccsb_service`, `ccsb_scheduleitem`, `ccsb_schedulerequirement`, `ccsb_scheduleassignment`, and `ccsb_conflict` are user/team-owned** so scheduling work can use standard Dataverse owner-based security if required.
3. **`ccsb_leave` stores only operational availability.** The base solution deliberately excludes medical, health, or sensitive leave-reason fields.
4. **`ccsb_publishsnapshot` and `ccsb_scheduleversion` are organization-owned** to treat published schedule evidence as governed shared data, not personally owned work items.
5. The base solution creates a primary-name field called **`ccsb_name`** on every table. It has table-specific display labels but the same logical field name because Dataverse attribute logical names only need to be unique within each table.

