from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "tools" / "developer" / "legacy-analysis" / "build_entity_design_optimization.py"
OUT = ROOT / "tools" / "provisioning" / "CCSB.AuditEntities" / "schema" / "csb.auditentities.schema.json"


CHOICES = {
    "ccsb_capabilitytype": ["Skill", "Certification", "Clearance", "Territory", "Facility Feature", "Equipment", "Capacity", "Custom"],
    "ccsb_capabilitysource": ["CCSB", "Field Service", "Project Operations", "External", "Manual"],
    "ccsb_proficiencylevel": ["None", "Beginner", "Intermediate", "Advanced", "Expert"],
    "ccsb_verificationstatus": ["Unverified", "Verified", "Expired", "Rejected", "Waived"],
    "ccsb_capabilitystatus": ["Active", "Inactive", "Superseded", "Archived"],
    "ccsb_actorprincipaltype": ["User", "Team", "Application User", "System", "Integration"],
    "ccsb_auditeventtype": ["Validation", "Command", "Security", "Publish", "Rollback", "Lock", "Integration", "Support", "System"],
    "ccsb_actiontype": ["Create", "Update", "Delete", "Approve", "Reject", "Publish", "Rollback", "Lock", "Unlock", "Dispatch"],
    "ccsb_outcome": ["Started", "Succeeded", "Failed", "Blocked", "Skipped", "Compensated"],
    "ccsb_severity": ["Information", "Warning", "Error", "Critical"],
    "ccsb_targetscopetype": ["Board", "Version", "Requirement", "Assignment", "Resource", "Group", "External"],
    "ccsb_reasoncategory": ["Policy", "User Request", "Conflict", "Integration", "Data Correction", "Support", "System"],
    "ccsb_changetype": ["Create", "Update", "Delete", "Move", "Assign", "Unassign", "Split", "Merge", "Rollback", "Publish"],
    "ccsb_changestatus": ["Proposed", "Validated", "Approved", "Committed", "Published", "Rejected", "Superseded", "Rolled Back", "Failed"],
    "ccsb_sourceorigin": ["User", "API", "Bulk Import", "Optimizer", "External Integration", "Rollback", "System"],
    "ccsb_snapshotitemtype": ["Schedule Item", "Assignment", "Requirement", "Resource", "Lock", "Metadata", "External Projection"],
    "ccsb_capturestatus": ["Captured", "Skipped", "Missing", "Transformed", "Failed"],
    "ccsb_locktype": ["Publish Protection", "Edit Freeze", "Rollback Protection", "Approval Hold", "External Dependency"],
    "ccsb_locklevel": ["Board", "Version", "Group", "Resource", "Item", "Field", "External"],
    "ccsb_lockstatus": ["Active", "Released", "Expired", "Overridden", "Superseded"],
    "ccsb_scopetype": ["Global Board", "Time Window", "Resource", "Requirement", "Assignment", "External"],
    "ccsb_eventtype": ["Published", "Changed", "Locked", "Unlocked", "Rollback", "Export", "Notification", "Integration Command"],
    "ccsb_eventstatus": ["Pending", "Processing", "Delivered", "Failed", "Dead Lettered", "Skipped", "Replayed"],
    "ccsb_destinationtype": ["Dataverse Event", "Power Automate", "Service Bus", "Event Grid", "Webhook", "Export", "Internal"],
}


def load_source():
    spec = importlib.util.spec_from_file_location("optimized_design", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to import {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_name(logical_name: str) -> str:
    if not logical_name.startswith("ccsb_"):
        return logical_name
    parts = logical_name.removeprefix("ccsb_").split("_")
    return "ccsb_" + "".join(part[:1].upper() + part[1:] for part in parts)


def table_schema_name(logical_name: str) -> str:
    return schema_name(logical_name)


def display_from_logical(logical_name: str) -> str:
    text = logical_name.removeprefix("ccsb_")
    text = re.sub(r"id$", "", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = text.replace("_", " ")
    words = []
    for word in text.split():
        if word.lower() == "utc":
            words.append("UTC")
        elif word.lower() == "json":
            words.append("JSON")
        elif word.lower() == "id":
            words.append("ID")
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def parse_max_length(constraint: str, default: int) -> int:
    match = re.search(r"Max\s+(\d+)", constraint or "", re.IGNORECASE)
    return int(match.group(1)) if match else default


def map_type(raw_type: str) -> str | None:
    lower = raw_type.lower()
    if lower in {"uniqueidentifier", "primary name"}:
        return None
    if lower.startswith("lookup"):
        return None
    if lower == "text":
        return "String"
    if lower == "multiline text":
        return "Memo"
    if lower == "choice":
        return "Choice"
    if lower == "decimal":
        return "Decimal"
    if lower == "whole number":
        return "Integer"
    if lower == "boolean":
        return "Boolean"
    if lower == "datetime":
        return "DateTime"
    raise ValueError(f"Unsupported optimized field type: {raw_type}")


def field_to_manifest(field: dict) -> dict | None:
    field_type = map_type(field["type"])
    if field_type is None:
        return None

    logical = field["logical"]
    spec = {
        "schemaName": schema_name(logical),
        "logicalName": logical,
        "displayName": display_from_logical(logical),
        "type": field_type,
        "description": field["purpose"],
        "required": field["required"].lower() == "yes",
        "isSecured": "security" in field["security"].lower(),
    }

    if field_type == "String":
        spec["maxLength"] = parse_max_length(field["constraint"], 200)
    elif field_type == "Memo":
        spec["maxLength"] = 100000
    elif field_type == "Choice":
        labels = CHOICES.get(logical)
        if labels is None:
            labels = ["Not Set", "Active", "Inactive", "Other"]
        spec["choiceOptions"] = [
            {"value": 831030000 + index, "label": label}
            for index, label in enumerate(labels)
        ]
    elif field_type == "Decimal":
        spec["precision"] = 2
        spec["minValue"] = -100000000
        spec["maxValue"] = 100000000
    elif field_type == "Integer":
        spec["minValue"] = 0
        spec["maxValue"] = 2147483647
    elif field_type == "Boolean":
        spec["defaultValue"] = False

    return spec


def key_field(entity: dict) -> str:
    return entity["keys"][0]


def status_fields(entity: dict) -> list[str]:
    suffixes = ("status", "outcome", "severity", "type", "level")
    return [
        field["logical"]
        for field in entity["fields"]
        if field["type"].lower() == "choice" and field["logical"].endswith(suffixes)
    ][:3]


def simple_field_names(entity: dict, kind: str) -> list[str]:
    result = []
    for field in entity["fields"]:
        raw_type = field["type"].lower()
        if kind == "memo" and raw_type == "multiline text":
            result.append(field["logical"])
        elif kind == "process" and raw_type in {"choice", "datetime", "decimal", "whole number", "boolean"}:
            result.append(field["logical"])
    return result


def relationship_fields(source: str, relationships: list[dict]) -> list[str]:
    return [rel["lookup"] for rel in relationships if rel["source"] == source]


def build_forms(entity: dict, relationships: list[dict]) -> dict:
    logical = entity["logical"]
    summary = ["ccsb_name", key_field(entity), *status_fields(entity)]
    process = [name for name in simple_field_names(entity, "process") if name not in summary]
    memos = simple_field_names(entity, "memo")
    lookups = relationship_fields(logical, relationships)
    admin = ["ownerid", "createdon", "createdby", "modifiedon", "modifiedby", "statecode", "statuscode"]

    sections = [
        {"tab": "General", "section": "Summary", "fields": summary[:8]},
        {"tab": "General", "section": "Relationships", "fields": lookups[:12]},
        {"tab": "Lifecycle", "section": "Process", "fields": process[:16]},
        {"tab": "Payload", "section": "Payload and Diagnostics", "fields": memos[:12]},
        {"tab": "Administration", "section": "Audit and Record State", "fields": admin},
    ]
    sections = [section for section in sections if section["fields"]]

    return {
        "mainForm": {
            "name": f"CSB - {entity['display']} Main",
            "sections": sections,
        }
    }


def build_views(entity: dict) -> list[dict]:
    key = key_field(entity)
    columns = ["ccsb_name", key, *status_fields(entity), "modifiedon"]
    columns = list(dict.fromkeys(columns))[:10]
    return [
        {
            "name": f"CSB - {entity['display']} - Active",
            "purpose": "Active audit/control records ordered by most recently modified.",
            "filter": {"field": "statecode", "operator": "eq", "value": "0"},
            "sort": {"field": "modifiedon", "descending": True},
            "columns": columns,
        },
        {
            "name": f"CSB - {entity['display']} - All Records",
            "purpose": "All audit/control records ordered by most recently modified.",
            "filter": None,
            "sort": {"field": "modifiedon", "descending": True},
            "columns": columns,
        },
    ]


def relationship_schema_name(rel: dict) -> str:
    lookup_role = rel["lookup"].removeprefix("ccsb_").removesuffix("id")
    source = rel["source"].removeprefix("ccsb_")
    target = rel["target"].removeprefix("ccsb_")
    return f"ccsb_{target}_{source}_{lookup_role}"


def build_manifest() -> dict:
    source = load_source()
    entities = source.ENTITIES
    relationships = source.RELATIONSHIPS

    tables = []
    for entity in entities:
        table = {
            "schemaName": table_schema_name(entity["logical"]),
            "logicalName": entity["logical"],
            "displayName": entity["display"],
            "collectionName": entity["display"] + "s",
            "ownership": entity["ownership"],
            "description": entity["decision"],
            "primaryName": {
                "schemaName": "ccsb_Name",
                "logicalName": "ccsb_name",
                "displayName": entity["display"] + " Name",
                "description": "Primary display name.",
                "maxLength": 300,
            },
            "fields": [
                converted
                for field in entity["fields"]
                if (converted := field_to_manifest(field)) is not None and converted["logicalName"] != "ccsb_name"
            ],
            "alternateKeys": [
                {
                    "schemaName": schema_name(key_field(entity)) + "Key",
                    "displayName": entity["display"] + " Key",
                    "fields": [key_field(entity)],
                }
            ],
        }
        table.update(build_forms(entity, relationships))
        table["views"] = build_views(entity)
        tables.append(table)

    rels = []
    for rel in relationships:
        rels.append(
            {
                "schemaName": relationship_schema_name(rel),
                "referencedEntity": rel["target"],
                "referencingEntity": rel["source"],
                "lookupSchemaName": schema_name(rel["lookup"]),
                "lookupLogicalName": rel["lookup"],
                "lookupDisplayName": display_from_logical(rel["lookup"]),
                "collectionLabel": display_from_logical(rel["source"]) + "s",
                "description": rel["why"],
                "required": rel["required"].lower() == "yes",
                "failIfTargetMissing": True,
            }
        )

    return {
        "schemaVersion": "1.0.0",
        "solution": {
            "uniqueName": "CSB_AuditEntities",
            "displayName": "CSB Audit Entities",
            "version": "1.0.0.0",
            "publisherPrefix": "ccsb",
            "publisherPreferredUniqueName": "CSB_AuditEntitiesPublisher",
            "publisherFriendlyName": "CSB Audit Entities Publisher",
            "description": "Unmanaged solution containing CCSB audit, publish, snapshot, lock, resource capability, and outbox entities.",
        },
        "tables": tables,
        "relationships": rels,
    }


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest()
    OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Tables: {len(manifest['tables'])}")
    print(f"Fields: {sum(len(table['fields']) for table in manifest['tables'])}")
    print(f"Relationships: {len(manifest['relationships'])}")


if __name__ == "__main__":
    main()

