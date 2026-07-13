#!/usr/bin/env python3
"""Static acceptance validator for US-070-T02 permission profile/assignment schema."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = ROOT / "tools" / "provisioning" / "CCSB.FoundationSchema" / "schema" / "ccsb.foundation.schema.json"
DEFAULT_SEED = ROOT / "tests" / "Fixtures" / "Schema" / "US-004-T09-seed-manifest.json"
DEFAULT_MATRIX = ROOT / "tests" / "Fixtures" / "Security" / "US-070-T01-permission-matrix.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-070-T02" / "static-report.md"

PROFILE_TABLE = "ccsb_permissionprofile"
ASSIGNMENT_TABLE = "ccsb_permissionassignment"
PROFILE_FLAGS = {
    "ccsb_canviewschedule",
    "ccsb_cancreateschedule",
    "ccsb_caneditschedule",
    "ccsb_canassignresources",
    "ccsb_canoverrideconflicts",
    "ccsb_canpublish",
    "ccsb_canrollback",
    "ccsb_canmanageconfiguration",
    "ccsb_canviewaudit",
    "ccsb_canmanageintegrations",
}
PROFILE_REQUIRED_FIELDS = PROFILE_FLAGS | {
    "ccsb_profilecode",
    "ccsb_description",
    "ccsb_profiletype",
    "ccsb_scopemode",
    "ccsb_dataverserolename",
    "ccsb_isenabled",
}
ASSIGNMENT_REQUIRED_FIELDS = {
    "ccsb_principaltype",
    "ccsb_principalid",
    "ccsb_principaldisplayname",
    "ccsb_accesseffect",
    "ccsb_scopetype",
    "ccsb_scopereferenceid",
    "ccsb_scopedisplayname",
    "ccsb_effectivefrom",
    "ccsb_effectiveto",
    "ccsb_approvalreference",
    "ccsb_isenabled",
}
REQUIRED_PROFILE_RELATIONSHIPS = {
    ("ccsb_boardversion", PROFILE_TABLE, "ccsb_boardversionid"),
}
REQUIRED_ASSIGNMENT_RELATIONSHIPS = {
    (PROFILE_TABLE, ASSIGNMENT_TABLE, "ccsb_permissionprofileid"),
    ("ccsb_boardregistry", ASSIGNMENT_TABLE, "ccsb_boardid"),
    ("ccsb_location", ASSIGNMENT_TABLE, "ccsb_locationid"),
    ("ccsb_groupnode", ASSIGNMENT_TABLE, "ccsb_groupnodeid"),
}
REQUIRED_PRINCIPAL_LABELS = {"System User", "Team", "Business Unit", "Entra Group"}
REQUIRED_ACCESS_EFFECT_LABELS = {"Grant", "Deny"}
REQUIRED_SCOPE_LABELS = {"All Boards", "Board", "Location", "Group Node", "Assigned Work"}
REQUIRED_PROFILE_TYPE_LABELS = {
    "Planner",
    "Dispatcher",
    "Resource Manager",
    "Release Manager",
    "Configuration Administrator",
    "Read Only",
    "Support",
}
REQUIRED_SCOPE_MODE_LABELS = {"All Boards", "Board", "Location", "Group", "Assigned Work"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def table_by_name(schema: dict[str, Any], logical_name: str) -> dict[str, Any] | None:
    for table in schema.get("tables", []):
        if table.get("logicalName") == logical_name:
            return table
    return None


def fields_by_name(table: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {field.get("logicalName"): field for field in table.get("fields", []) if isinstance(field.get("logicalName"), str)}


def choice_labels(field: dict[str, Any]) -> set[str]:
    return {option.get("label") for option in field.get("choiceOptions", []) if isinstance(option.get("label"), str)}


def relationship_keys(schema: dict[str, Any]) -> set[tuple[str, str, str]]:
    return {
        (rel.get("referencedEntity"), rel.get("referencingEntity"), rel.get("lookupLogicalName"))
        for rel in schema.get("relationships", [])
    }


def validate_schema(schema: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, int]:
    profile = table_by_name(schema, PROFILE_TABLE)
    assignment = table_by_name(schema, ASSIGNMENT_TABLE)
    if profile is None:
        errors.append("CCSB-T02-PROFILE-TABLE: ccsb_permissionprofile table is missing.")
        return {}
    if assignment is None:
        errors.append("CCSB-T02-ASSIGNMENT-TABLE: ccsb_permissionassignment table is missing.")
        return {}

    if profile.get("ownership") != "UserOwned":
        errors.append("CCSB-T02-PROFILE-OWNERSHIP: Permission Profile must be UserOwned.")
    if assignment.get("ownership") != "UserOwned":
        errors.append("CCSB-T02-ASSIGNMENT-OWNERSHIP: Permission Assignment must be UserOwned.")
    description = " ".join([profile.get("description", ""), assignment.get("description", ""), " ".join(schema.get("notes", []))]).lower()
    for marker in ("dataverse", "security", "scope"):
        if marker not in description:
            errors.append(f"CCSB-T02-SECURITY-DESCRIPTION: Schema description/notes must mention {marker}.")

    profile_fields = fields_by_name(profile)
    assignment_fields = fields_by_name(assignment)
    missing_profile = PROFILE_REQUIRED_FIELDS - set(profile_fields)
    missing_assignment = ASSIGNMENT_REQUIRED_FIELDS - set(assignment_fields)
    if missing_profile:
        errors.append(f"CCSB-T02-PROFILE-FIELDS: Missing profile fields {sorted(missing_profile)}.")
    if missing_assignment:
        errors.append(f"CCSB-T02-ASSIGNMENT-FIELDS: Missing assignment fields {sorted(missing_assignment)}.")

    for flag in sorted(PROFILE_FLAGS):
        field = profile_fields.get(flag, {})
        if field.get("type") != "Boolean" or field.get("required") is not True:
            errors.append(f"CCSB-T02-PROFILE-FLAG: {flag} must be a required Boolean field.")
        if "defaultValue" not in field:
            errors.append(f"CCSB-T02-PROFILE-FLAG-DEFAULT: {flag} must declare a defaultValue.")
    for field_name in ("ccsb_profilecode", "ccsb_profiletype", "ccsb_scopemode", "ccsb_isenabled"):
        if profile_fields.get(field_name, {}).get("required") is not True:
            errors.append(f"CCSB-T02-PROFILE-REQUIRED: {field_name} must be required.")
    if profile_fields.get("ccsb_profilecode", {}).get("type") != "String":
        errors.append("CCSB-T02-PROFILE-CODE: ccsb_profilecode must be String.")
    if not any(key.get("fields") == ["ccsb_profilecode"] for key in profile.get("alternateKeys", [])):
        errors.append("CCSB-T02-PROFILE-KEY: ccsb_profilecode alternate key is required.")
    if REQUIRED_PROFILE_TYPE_LABELS - choice_labels(profile_fields.get("ccsb_profiletype", {})):
        errors.append("CCSB-T02-PROFILE-TYPE: profiletype choices do not cover required personas.")
    if REQUIRED_SCOPE_MODE_LABELS - choice_labels(profile_fields.get("ccsb_scopemode", {})):
        errors.append("CCSB-T02-SCOPE-MODE: scopemode choices do not cover required scope modes.")

    for field_name in ("ccsb_principaltype", "ccsb_principalid", "ccsb_accesseffect", "ccsb_scopetype", "ccsb_isenabled"):
        if assignment_fields.get(field_name, {}).get("required") is not True:
            errors.append(f"CCSB-T02-ASSIGNMENT-REQUIRED: {field_name} must be required.")
    if assignment_fields.get("ccsb_principalid", {}).get("type") != "String":
        errors.append("CCSB-T02-PRINCIPAL-ID: ccsb_principalid must be String for polymorphic portability.")
    if REQUIRED_PRINCIPAL_LABELS - choice_labels(assignment_fields.get("ccsb_principaltype", {})):
        errors.append("CCSB-T02-PRINCIPAL-TYPE: principaltype choices are incomplete.")
    if REQUIRED_ACCESS_EFFECT_LABELS - choice_labels(assignment_fields.get("ccsb_accesseffect", {})):
        errors.append("CCSB-T02-ACCESS-EFFECT: Grant and Deny access effects are required.")
    if REQUIRED_SCOPE_LABELS - choice_labels(assignment_fields.get("ccsb_scopetype", {})):
        errors.append("CCSB-T02-SCOPE-TYPE: assignment scope choices are incomplete.")
    if assignment_fields.get("ccsb_isenabled", {}).get("defaultValue") is not True:
        errors.append("CCSB-T02-ASSIGNMENT-ENABLED: ccsb_isenabled must default true.")

    rels = relationship_keys(schema)
    missing_profile_rels = REQUIRED_PROFILE_RELATIONSHIPS - rels
    missing_assignment_rels = REQUIRED_ASSIGNMENT_RELATIONSHIPS - rels
    if missing_profile_rels:
        errors.append(f"CCSB-T02-PROFILE-RELATIONSHIPS: Missing relationships {sorted(missing_profile_rels)}.")
    if missing_assignment_rels:
        errors.append(f"CCSB-T02-ASSIGNMENT-RELATIONSHIPS: Missing relationships {sorted(missing_assignment_rels)}.")

    secretish = [field for field in set(profile_fields) | set(assignment_fields) if any(token in field for token in ("secret", "token", "password", "connectionstring"))]
    if secretish:
        errors.append(f"CCSB-T02-NO-SECRETS: Permission schema must not store secrets/tokens: {sorted(secretish)}.")

    return {
        "profileFields": len(profile_fields),
        "assignmentFields": len(assignment_fields),
        "profileFlags": len(PROFILE_FLAGS & set(profile_fields)),
        "relationships": len([rel for rel in rels if rel[1] in {PROFILE_TABLE, ASSIGNMENT_TABLE}]),
    }


def validate_seed(seed: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, int]:
    required_coverage = set(seed.get("requiredEntityCoverage", []))
    for entity in (PROFILE_TABLE, ASSIGNMENT_TABLE):
        if entity not in required_coverage:
            errors.append(f"CCSB-T02-SEED-COVERAGE: {entity} missing from requiredEntityCoverage.")
    records = seed.get("records", [])
    profile_records = [record for record in records if record.get("entity") == PROFILE_TABLE]
    assignment_records = [record for record in records if record.get("entity") == ASSIGNMENT_TABLE]
    if not profile_records:
        errors.append("CCSB-T02-SEED-PROFILE: At least one permission profile seed is required.")
    if not assignment_records:
        errors.append("CCSB-T02-SEED-ASSIGNMENT: At least one permission assignment seed is required.")
    for record in profile_records:
        attrs = record.get("attributes", {})
        missing = PROFILE_FLAGS - set(attrs)
        if missing:
            errors.append(f"CCSB-T02-SEED-PROFILE-FLAGS: {record.get('id')} missing flags {sorted(missing)}.")
        if not any(ref.get("field") == "ccsb_boardversionid" for ref in record.get("references", [])):
            errors.append(f"CCSB-T02-SEED-PROFILE-SCOPE: {record.get('id')} must reference board version.")
    for record in assignment_records:
        attrs = record.get("attributes", {})
        for field in ("ccsb_principaltype", "ccsb_principalid", "ccsb_accesseffect", "ccsb_scopetype", "ccsb_isenabled"):
            if field not in attrs:
                errors.append(f"CCSB-T02-SEED-ASSIGNMENT-FIELD: {record.get('id')} missing {field}.")
        refs = {ref.get("field") for ref in record.get("references", [])}
        if "ccsb_permissionprofileid" not in refs:
            errors.append(f"CCSB-T02-SEED-ASSIGNMENT-PROFILE: {record.get('id')} must reference permission profile.")
        if not ({"ccsb_boardid", "ccsb_locationid", "ccsb_groupnodeid"} & refs):
            errors.append(f"CCSB-T02-SEED-ASSIGNMENT-SCOPE: {record.get('id')} should include a concrete board/location/group scope reference.")
    _ = warnings
    return {"seedProfiles": len(profile_records), "seedAssignments": len(assignment_records)}


def validate_matrix(matrix_path: Path, errors: list[str], warnings: list[str]) -> dict[str, int]:
    if not matrix_path.exists():
        return {"matrixFlags": 0}
    matrix = read_json(matrix_path)
    flags = {action.get("profileFlag") for action in matrix.get("actions", [])}
    missing = PROFILE_FLAGS - flags
    if missing:
        errors.append(f"CCSB-T02-T01-FLAG-CONTINUITY: T01 matrix is missing profile flags {sorted(missing)}.")
    return {"matrixFlags": len(flags & PROFILE_FLAGS)}


def validate(schema_path: Path, seed_path: Path, matrix_path: Path) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    schema = read_json(schema_path)
    seed = read_json(seed_path)
    counts: dict[str, int] = {}
    counts.update(validate_schema(schema, errors, warnings))
    counts.update(validate_seed(seed, errors, warnings))
    counts.update(validate_matrix(matrix_path, errors, warnings))
    return errors, warnings, counts


def write_report(path: Path, schema_path: Path, seed_path: Path, matrix_path: Path, errors: list[str], warnings: list[str], counts: dict[str, int]) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# US-070-T02 Static Permission Schema Validation Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated}",
        f"**Schema:** `{schema_path.relative_to(ROOT).as_posix()}`",
        f"**Seed manifest:** `{seed_path.relative_to(ROOT).as_posix()}`",
        f"**Permission matrix:** `{matrix_path.relative_to(ROOT).as_posix()}`",
        "",
        "## Counts",
        "",
        f"- Permission profile fields: {counts.get('profileFields', 0)}",
        f"- Permission assignment fields: {counts.get('assignmentFields', 0)}",
        f"- Profile action flags: {counts.get('profileFlags', 0)}",
        f"- Permission relationships: {counts.get('relationships', 0)}",
        f"- Seed profiles: {counts.get('seedProfiles', 0)}",
        f"- Seed assignments: {counts.get('seedAssignments', 0)}",
        f"- T01 matrix flags covered: {counts.get('matrixFlags', 0)}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Validation Scope",
        "",
        "- `ccsb_permissionprofile` table presence, ownership, profile code key, profile type, scope mode, enabled flag, and action flags",
        "- `ccsb_permissionassignment` table presence, ownership, principal fields, access effect, scope type, effective dates, approval reference, and enabled flag",
        "- Board-version, profile, board, location, and group-node scope relationships",
        "- Deterministic seed coverage for profile and assignment rows",
        "- Continuity with the US-070-T01 action matrix profile flags when the matrix is present on the branch",
        "- No secret/token/password/connection-string fields in permission schema",
        "",
        "## Issues",
        "",
    ]
    if not errors and not warnings:
        lines.append("- None")
    for issue in errors:
        parts = issue.split(":", 1)
        lines.append(f"- [ERROR] `{parts[0]}` - {parts[1].strip() if len(parts) > 1 else issue}")
    for issue in warnings:
        parts = issue.split(":", 1)
        lines.append(f"- [WARNING] `{parts[0]}` - {parts[1].strip() if len(parts) > 1 else issue}")
    lines.extend([
        "",
        "## Boundary",
        "",
        "This report proves the static schema and seed contract for US-070-T02. Runtime authorization logic remains US-070-T03, permission-aware UI behavior remains US-070-T04, connected role-matrix tests remain US-070-T05, and managed-solution role packaging remains US-070-T06.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate US-070-T02 permission profile and assignment schema.")
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--seed", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    schema_path = args.schema.resolve()
    seed_path = args.seed.resolve()
    matrix_path = args.matrix.resolve()
    errors, warnings, counts = validate(schema_path, seed_path, matrix_path)
    write_report(args.report.resolve(), schema_path, seed_path, matrix_path, errors, warnings, counts)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        for issue in errors:
            print(issue)
        return 1
    print(
        f"OK: {counts.get('profileFlags', 0)} profile flags, "
        f"{counts.get('relationships', 0)} permission relationship(s), "
        f"{counts.get('seedProfiles', 0)} seed profile(s), "
        f"{len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
