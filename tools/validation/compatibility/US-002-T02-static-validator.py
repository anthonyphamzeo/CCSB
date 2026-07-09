#!/usr/bin/env python3
"""Static validator for US-002-T02 compatibility metadata persistence."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "docs" / "design" / "data-model" / "compatibility" / "US-002-T02-compatibility-metadata.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-002-T02" / "static-report.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
BOARD_FIELDS = {"ccsb_productversion", "ccsb_configurationschemaversion", "ccsb_migrationstate", "ccsb_compatibilitystatus"}
PROJECTION_FIELDS = {"ccsb_productversion", "ccsb_configurationschemaversion", "ccsb_projectionschemaversion"}
MIGRATION_LABELS = {"None", "Pending", "Running", "Completed", "Failed", "Blocked"}
COMPAT_LABELS = {"Not Evaluated", "Compatible", "Compatible With Warnings", "Incompatible", "Migration Required", "Blocked"}
DIAGNOSTICS = {"CCSB-COMPAT-METADATA-MISSING", "CCSB-COMPAT-PROJECTION-METADATA-MISMATCH"}
GATES = {
    "board-version-product-version-field-present",
    "board-version-configuration-schema-version-field-present",
    "board-version-migration-state-field-present",
    "board-version-compatibility-status-field-present",
    "runtime-projection-product-version-field-present",
    "runtime-projection-configuration-schema-version-field-present",
    "active-board-version-invariant-declared",
    "current-projection-invariant-declared",
    "metadata-backfill-plan-declared",
    "static-validator-pass",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def schema_fields(schema: dict, entity: str) -> dict:
    for table in schema.get("tables", []):
        if table.get("logicalName") == entity:
            return {field["logicalName"]: field for field in table.get("fields", []) if "logicalName" in field}
    return {}


def labels(field: dict) -> set[str]:
    return {option.get("label") for option in field.get("choiceOptions", [])}


def validate(contract_path: Path) -> tuple[dict, list[str], list[str], dict[str, dict]]:
    errors: list[str] = []
    warnings: list[str] = []
    contract = read_json(contract_path)

    if contract.get("task") != "US-002-T02":
        errors.append("CCSB-T02-TASK-ID: Contract task must be US-002-T02.")
    if not isinstance(contract.get("manifestVersion"), str) or not SEMVER.match(contract["manifestVersion"]):
        errors.append("CCSB-T02-MANIFEST-VERSION: manifestVersion must be semantic version x.y.z.")

    doc_value = contract.get("metadataDocument")
    doc_path = ROOT / doc_value if isinstance(doc_value, str) else None
    if not doc_path or not doc_path.exists():
        errors.append("CCSB-T02-DOCUMENT-MISSING: metadataDocument is missing.")
    else:
        doc_text = doc_path.read_text(encoding="utf-8-sig")
        for phrase in ("Field Bindings", "Active Board Version", "Current Projection", "Done Evidence"):
            if phrase not in doc_text:
                errors.append(f"CCSB-T02-DOCUMENT-COVERAGE: metadata document missing {phrase}.")

    t01_value = contract.get("sourceCompatibilityContract")
    t01_path = ROOT / t01_value if isinstance(t01_value, str) else None
    if not t01_path or not t01_path.exists():
        errors.append("CCSB-T02-T01-MISSING: sourceCompatibilityContract is missing.")
        t01 = {}
    else:
        t01 = read_json(t01_path)
        if t01.get("task") != "US-002-T01":
            errors.append("CCSB-T02-T01-TASK: sourceCompatibilityContract must point to US-002-T01.")
        if contract.get("versionDimensions") != t01.get("versionDimensions"):
            errors.append("CCSB-T02-VERSION-DIMENSIONS: T02 versions must match T01.")

    schema_value = contract.get("sourcePackage", {}).get("schema")
    schema_path = ROOT / schema_value if isinstance(schema_value, str) else None
    if not schema_path or not schema_path.exists():
        errors.append("CCSB-T02-SCHEMA-MISSING: sourcePackage.schema is missing.")
        schema = {}
    else:
        schema = read_json(schema_path)
        if schema.get("schemaVersion") != contract.get("sourcePackage", {}).get("schemaVersion"):
            errors.append("CCSB-T02-SCHEMA-VERSION: sourcePackage.schemaVersion must match schema JSON.")
        if schema.get("solution", {}).get("version") != contract.get("sourcePackage", {}).get("targetSolutionVersion"):
            errors.append("CCSB-T02-SOLUTION-VERSION: targetSolutionVersion must match schema JSON.")

    observed = {
        "ccsb_boardversion": schema_fields(schema, "ccsb_boardversion"),
        "ccsb_runtimeprojection": schema_fields(schema, "ccsb_runtimeprojection"),
    }
    if BOARD_FIELDS - set(observed["ccsb_boardversion"]):
        errors.append(f"CCSB-T02-BOARD-FIELDS: Missing board fields {sorted(BOARD_FIELDS - set(observed['ccsb_boardversion']))}.")
    if PROJECTION_FIELDS - set(observed["ccsb_runtimeprojection"]):
        errors.append(f"CCSB-T02-PROJECTION-FIELDS: Missing projection fields {sorted(PROJECTION_FIELDS - set(observed['ccsb_runtimeprojection']))}.")

    binding_entities = {binding.get("entity") for binding in contract.get("metadataBindings", [])}
    if binding_entities != {"ccsb_boardversion", "ccsb_runtimeprojection"}:
        errors.append("CCSB-T02-BINDING-ENTITIES: metadataBindings must cover board version and runtime projection.")
    for binding in contract.get("metadataBindings", []):
        entity = binding.get("entity")
        fields = observed.get(entity, {})
        for expected in binding.get("fields", []):
            name = expected.get("logicalName")
            actual = fields.get(name)
            if not actual:
                errors.append(f"CCSB-T02-BINDING-FIELD: Missing {entity}.{name}.")
                continue
            if actual.get("type") != expected.get("type"):
                errors.append(f"CCSB-T02-BINDING-TYPE: {entity}.{name} has wrong type.")
            if actual.get("schemaName") != expected.get("schemaName"):
                errors.append(f"CCSB-T02-BINDING-SCHEMA: {entity}.{name} has wrong schemaName.")
            if expected.get("requiredAtMetadataLevel") is False and actual.get("required") is not False:
                errors.append(f"CCSB-T02-BINDING-REQUIREDNESS: {entity}.{name} must remain optional at metadata level.")
            if "maxLength" in expected and actual.get("maxLength", expected["maxLength"]) < expected["maxLength"]:
                errors.append(f"CCSB-T02-BINDING-MAXLENGTH: {entity}.{name} maxLength is too small.")
            missing_labels = set(expected.get("allowedLabels", [])) - labels(actual)
            if missing_labels:
                errors.append(f"CCSB-T02-BINDING-CHOICES: {entity}.{name} missing choices {sorted(missing_labels)}.")

    if not MIGRATION_LABELS.issubset(labels(observed["ccsb_boardversion"].get("ccsb_migrationstate", {}))):
        errors.append("CCSB-T02-MIGRATION-LABELS: migration state choices are incomplete.")
    if not COMPAT_LABELS.issubset(labels(observed["ccsb_boardversion"].get("ccsb_compatibilitystatus", {}))):
        errors.append("CCSB-T02-COMPATIBILITY-LABELS: compatibility status choices are incomplete.")

    active = contract.get("activeBoardVersionInvariant", {})
    if not BOARD_FIELDS.issubset(set(active.get("requiredNonNullFields", []))):
        errors.append("CCSB-T02-ACTIVE-INVARIANT: active invariant must require all board compatibility fields.")
    if set(active.get("allowedMigrationStateLabelsForActivation", [])) != {"None", "Completed"}:
        errors.append("CCSB-T02-ACTIVE-MIGRATION: active versions may only allow None or Completed migration states.")
    if set(active.get("allowedCompatibilityStatusLabelsForActivation", [])) != {"Compatible", "Compatible With Warnings"}:
        errors.append("CCSB-T02-ACTIVE-COMPATIBILITY: active versions have invalid compatibility statuses.")

    current = contract.get("currentProjectionInvariant", {})
    if not PROJECTION_FIELDS.issubset(set(current.get("requiredNonNullFields", []))):
        errors.append("CCSB-T02-PROJECTION-INVARIANT: current projection invariant must require all projection fields.")
    for field in ("ccsb_productversion", "ccsb_configurationschemaversion"):
        if current.get("mustMatchBoardVersionFields", {}).get(field) != field:
            errors.append(f"CCSB-T02-PROJECTION-MATCH: current projection must match board {field}.")

    covered = set()
    for item in contract.get("backfillPlan", []):
        covered.update(item.get("fields", []))
        if item.get("idempotent") is not True or item.get("activationBlocking") is not True:
            errors.append(f"CCSB-T02-BACKFILL: {item.get('id', '<unknown>')} must be idempotent and activation blocking.")
    missing_backfill = (BOARD_FIELDS | PROJECTION_FIELDS) - covered
    if missing_backfill:
        errors.append(f"CCSB-T02-BACKFILL-COVERAGE: backfill plan missing {sorted(missing_backfill)}.")

    actual_diagnostics = {item.get("code") for item in contract.get("diagnosticCodes", [])}
    if DIAGNOSTICS - actual_diagnostics:
        errors.append(f"CCSB-T02-DIAGNOSTICS: missing diagnostics {sorted(DIAGNOSTICS - actual_diagnostics)}.")
    if GATES - set(contract.get("acceptanceGates", [])):
        errors.append(f"CCSB-T02-GATES: missing gates {sorted(GATES - set(contract.get('acceptanceGates', [])))}.")
    return contract, errors, warnings, observed


def write_report(path: Path, contract_path: Path, contract: dict, errors: list[str], warnings: list[str], observed: dict[str, dict]) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# US-002-T02 Static Compatibility Metadata Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated}",
        f"**Contract:** `{contract_path.relative_to(ROOT).as_posix()}`",
        "",
        "## Counts",
        "",
        f"- Metadata binding groups: {len(contract.get('metadataBindings', []))}",
        f"- Board-version schema fields observed: {len(observed.get('ccsb_boardversion', {}))}",
        f"- Runtime-projection schema fields observed: {len(observed.get('ccsb_runtimeprojection', {}))}",
        f"- Backfill rules: {len(contract.get('backfillPlan', []))}",
        f"- Diagnostic codes: {len(contract.get('diagnosticCodes', []))}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Validation Scope",
        "",
        "- T02 contract, metadata document, and T01 compatibility linkage",
        "- Board-version and runtime-projection schema field bindings",
        "- Migration-state and compatibility-status choice coverage",
        "- Active board-version and current-projection invariants",
        "- Backfill plan, diagnostics, and acceptance gates",
        "",
        "## Issues",
        "",
    ]
    if not errors and not warnings:
        lines.append("- None")
    for issue in errors:
        lines.append(f"- [ERROR] `{issue.split(':', 1)[0]}` - {issue.split(':', 1)[1].strip() if ':' in issue else issue}")
    for issue in warnings:
        lines.append(f"- [WARNING] `{issue.split(':', 1)[0]}` - {issue.split(':', 1)[1].strip() if ':' in issue else issue}")
    lines.extend(["", "## Boundary", "", "This is static schema and contract validation. Runtime Custom API validation, connected Dataverse backfill execution, and activation enforcement remain downstream implementation work.", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the US-002-T02 compatibility metadata contract.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    contract, errors, warnings, observed = validate(args.contract.resolve())
    write_report(args.report.resolve(), args.contract.resolve(), contract, errors, warnings, observed)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        for issue in errors:
            print(issue)
        return 1
    print(f"OK: {len(contract.get('metadataBindings', []))} binding groups, {len(contract.get('backfillPlan', []))} backfill rules, {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
