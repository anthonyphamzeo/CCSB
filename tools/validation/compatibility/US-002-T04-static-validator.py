#!/usr/bin/env python3
"""Static acceptance validator for US-002-T04 administrator diagnostics."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "docs" / "design" / "ux" / "compatibility" / "US-002-T04-administrator-diagnostics.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-002-T04" / "static-report.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

REQUIRED_SURFACES = {
    "T04-SURFACE-001",
    "T04-SURFACE-002",
    "T04-SURFACE-003",
    "T04-SURFACE-004",
    "T04-SURFACE-005",
    "T04-SURFACE-006",
}
REQUIRED_GATES = {
    "admin-can-see-compatibility-state",
    "blocking-record-grid-scoped-to-board-version",
    "every-diagnostic-has-readable-action",
    "migration-action-visible-without-server-logs",
    "safe-revalidation-command-defined",
    "revalidation-does-not-call-activation",
    "revalidation-has-idempotency-key",
    "operation-evidence-visible",
    "runtime-projection-health-visible",
    "schema-bindings-validated",
    "relationship-bindings-validated",
    "t03-diagnostic-catalog-covered",
    "static-validator-pass",
}
REQUIRED_FIELD_BINDINGS = {
    "ccsb_boardversion": {
        "ccsb_lifecyclestate",
        "ccsb_validationstatus",
        "ccsb_validationrunon",
        "ccsb_compatibilitystatus",
        "ccsb_productversion",
        "ccsb_configurationschemaversion",
        "ccsb_migrationstate",
        "ccsb_configurationhash",
    },
    "ccsb_configurationvalidationresult": {
        "ccsb_validationrunid",
        "ccsb_validationcode",
        "ccsb_validationcategory",
        "ccsb_severity",
        "ccsb_resultstatus",
        "ccsb_affectedentitylogicalname",
        "ccsb_affectedrecordid",
        "ccsb_affectedfieldlogicalname",
        "ccsb_message",
        "ccsb_detailjson",
        "ccsb_recommendedaction",
        "ccsb_detectedon",
    },
    "ccsb_runtimeprojection": {
        "ccsb_projectionstatus",
        "ccsb_productversion",
        "ccsb_configurationschemaversion",
        "ccsb_projectionschemaversion",
        "ccsb_sourcechangetoken",
        "ccsb_contenthash",
        "ccsb_generatedon",
        "ccsb_iscurrent",
        "ccsb_errordetail",
    },
    "ccsb_operation": {
        "ccsb_operationtype",
        "ccsb_operationstatus",
        "ccsb_correlationid",
        "ccsb_idempotencykey",
        "ccsb_requestedon",
        "ccsb_startedon",
        "ccsb_completedon",
        "ccsb_resultjson",
        "ccsb_errorsummary",
        "ccsb_errordetail",
    },
}
REQUIRED_RELATIONSHIPS = {
    "ccsb_boardversion_ccsb_configurationvalidationresult",
    "ccsb_operation_ccsb_configurationvalidationresult",
    "ccsb_boardversion_ccsb_runtimeprojection",
    "ccsb_boardversion_ccsb_operation",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def linked_path(contract: dict[str, Any], key: str, errors: list[str]) -> Path | None:
    value = contract.get(key)
    if not isinstance(value, str):
        errors.append(f"CCSB-T04-LINK: {key} must be a repository-relative path.")
        return None
    path = (ROOT / value).resolve()
    try:
        path.relative_to(ROOT)
    except ValueError:
        errors.append(f"CCSB-T04-LINK-SCOPE: {key} must stay under sources/: {value}.")
        return None
    if not path.exists():
        errors.append(f"CCSB-T04-LINK-MISSING: {key} does not exist: {value}.")
        return None
    return path


def schema_fields(schema: dict[str, Any], entity: str) -> set[str]:
    for table in schema.get("tables", []):
        if table.get("logicalName") == entity:
            fields = {field.get("logicalName") for field in table.get("fields", [])}
            fields.add(f"{entity}id")
            fields.add("ccsb_name")
            return {field for field in fields if isinstance(field, str)}
    return set()


def schema_relationships(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        rel.get("schemaName"): rel
        for rel in schema.get("relationships", [])
        if isinstance(rel.get("schemaName"), str)
    }


def ensure_columns_bound(
    entity: str,
    columns: list[str],
    available_fields: dict[str, set[str]],
    lookups: dict[str, set[str]],
    errors: list[str],
    context: str,
) -> None:
    available = available_fields.get(entity, set()) | lookups.get(entity, set())
    missing = set(columns) - available
    if missing:
        errors.append(f"CCSB-T04-COLUMNS: {context}/{entity} has unbound columns {sorted(missing)}.")


def validate(contract_path: Path) -> tuple[dict[str, Any], list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    contract = read_json(contract_path)

    if contract.get("task") != "US-002-T04":
        errors.append("CCSB-T04-TASK-ID: Contract task must be US-002-T04.")
    if not isinstance(contract.get("manifestVersion"), str) or not SEMVER.match(contract["manifestVersion"]):
        errors.append("CCSB-T04-MANIFEST-VERSION: manifestVersion must be semantic version x.y.z.")

    document_path = linked_path(contract, "diagnosticsDocument", errors)
    linked_path(contract, "sourceCompatibilityContract", errors)
    linked_path(contract, "sourceMetadataContract", errors)
    t03_path = linked_path(contract, "sourcePreActivationContract", errors)
    schema_path = linked_path(contract, "sourceSchema", errors)

    if document_path:
        document = document_path.read_text(encoding="utf-8-sig")
        for heading in (
            "Scope",
            "Admin Workflow",
            "Compatibility State Summary",
            "Blocking Diagnostics Grid",
            "Migration And Remediation Actions",
            "Safe Re-validation Command",
            "Evidence And Audit",
            "Security And UX Rules",
            "Data And Schema Bindings",
            "Validation",
        ):
            if f"## {heading}" not in document:
                errors.append(f"CCSB-T04-DOCUMENT-COVERAGE: Missing heading: {heading}.")
        for marker in ("ccsb_ValidateBoardVersion", "ccsb_configurationvalidationresult", "server logs"):
            if marker not in document:
                errors.append(f"CCSB-T04-DOCUMENT-MARKER: Document must mention {marker}.")

    principles = contract.get("diagnosticPrinciples", {})
    if principles.get("serverLogsRequired") is not False:
        errors.append("CCSB-T04-SERVER-LOGS: Diagnostics must not require server logs.")
    if principles.get("showHumanReadableActionForEveryDiagnostic") is not True:
        errors.append("CCSB-T04-ACTIONS: Every diagnostic must have a human-readable action.")
    if principles.get("separateValidationFromActivation") is not True:
        errors.append("CCSB-T04-SEPARATION: Validation and activation must remain separate.")
    if principles.get("colorIsSupplementaryOnly") is not True:
        errors.append("CCSB-T04-COLOR: Color cannot be the only status channel.")
    if principles.get("rawJsonIsSupplementaryOnly") is not True:
        errors.append("CCSB-T04-RAW-JSON: Raw JSON cannot be required for primary remediation.")

    schema: dict[str, Any] | None = read_json(schema_path) if schema_path else None
    available_fields: dict[str, set[str]] = {}
    relationships: dict[str, dict[str, Any]] = {}
    if schema is not None:
        relationships = schema_relationships(schema)
        for entity in REQUIRED_FIELD_BINDINGS:
            available_fields[entity] = schema_fields(schema, entity)
            if not available_fields[entity]:
                errors.append(f"CCSB-T04-SCHEMA-ENTITY: Missing entity {entity}.")

    declared_fields = {
        entity: set(fields)
        for entity, fields in contract.get("fieldBindings", {}).items()
        if isinstance(fields, list)
    }
    for entity, required in REQUIRED_FIELD_BINDINGS.items():
        missing_declared = required - declared_fields.get(entity, set())
        if missing_declared:
            errors.append(f"CCSB-T04-FIELD-BINDINGS: {entity} missing declared fields {sorted(missing_declared)}.")
        missing_schema = declared_fields.get(entity, set()) - available_fields.get(entity, set())
        if missing_schema:
            errors.append(f"CCSB-T04-SCHEMA-FIELDS: {entity} fields missing from schema {sorted(missing_schema)}.")

    declared_lookups: dict[str, set[str]] = {}
    declared_relationships: set[str] = set()
    for lookup in contract.get("lookupBindings", []):
        entity = lookup.get("entity")
        lookup_name = lookup.get("lookupLogicalName")
        relationship = lookup.get("relationship")
        if not isinstance(entity, str) or not isinstance(lookup_name, str) or not isinstance(relationship, str):
            errors.append("CCSB-T04-LOOKUP-BINDING: Lookup binding must declare entity, lookupLogicalName, and relationship.")
            continue
        declared_lookups.setdefault(entity, set()).add(lookup_name)
        declared_relationships.add(relationship)
        schema_relationship = relationships.get(relationship)
        if not schema_relationship:
            errors.append(f"CCSB-T04-RELATIONSHIP-MISSING: Missing relationship {relationship}.")
            continue
        if schema_relationship.get("referencingEntity") != entity:
            errors.append(
                f"CCSB-T04-RELATIONSHIP-ENTITY: {relationship} should reference from {entity}."
            )
        if schema_relationship.get("lookupLogicalName") != lookup_name:
            errors.append(
                f"CCSB-T04-RELATIONSHIP-LOOKUP: {relationship} lookup should be {lookup_name}."
            )
    if REQUIRED_RELATIONSHIPS - declared_relationships:
        errors.append(
            f"CCSB-T04-RELATIONSHIP-BINDINGS: Missing relationships {sorted(REQUIRED_RELATIONSHIPS - declared_relationships)}."
        )

    surface_ids = {surface.get("id") for surface in contract.get("workspaceSurfaces", [])}
    if surface_ids != REQUIRED_SURFACES:
        errors.append(
            f"CCSB-T04-SURFACES: missing={sorted(REQUIRED_SURFACES - surface_ids)} "
            f"unexpected={sorted(surface_ids - REQUIRED_SURFACES)}."
        )
    for surface in contract.get("workspaceSurfaces", []):
        if not surface.get("adminOutcome"):
            errors.append(f"CCSB-T04-SURFACE-OUTCOME: {surface.get('id')} must define adminOutcome.")

    for view in contract.get("diagnosticViews", []):
        entity = view.get("entity")
        if not isinstance(entity, str):
            errors.append(f"CCSB-T04-VIEW-ENTITY: {view.get('id')} has invalid entity.")
            continue
        columns = view.get("columns", [])
        if not isinstance(columns, list) or not columns:
            errors.append(f"CCSB-T04-VIEW-COLUMNS: {view.get('id')} must have columns.")
            continue
        ensure_columns_bound(entity, columns, available_fields, declared_lookups, errors, str(view.get("id")))
        if entity == "ccsb_configurationvalidationresult":
            required = {"ccsb_validationcode", "ccsb_recommendedaction", "ccsb_affectedrecordid"}
            if required - set(columns):
                errors.append(f"CCSB-T04-BLOCKING-VIEW: {view.get('id')} lacks core diagnostic columns.")
            view_filter = view.get("filter", {})
            if view_filter.get("boardVersionScoped") is not True:
                errors.append(f"CCSB-T04-VIEW-SCOPE: {view.get('id')} must be board-version scoped.")

    t03_codes: set[str] = set()
    if t03_path:
        t03 = read_json(t03_path)
        if t03.get("activationIntegration", {}).get("validationConsumer") != "ccsb_ValidateBoardVersion":
            errors.append("CCSB-T04-T03-CONSUMER: T03 validation consumer continuity failed.")
        t03_codes = {item.get("code") for item in t03.get("diagnosticCatalog", []) if isinstance(item.get("code"), str)}
    action_map = contract.get("diagnosticActionMap", [])
    action_codes = {item.get("code") for item in action_map}
    if t03_codes - action_codes:
        errors.append(f"CCSB-T04-DIAGNOSTIC-COVERAGE: Missing actions for {sorted(t03_codes - action_codes)}.")
    for action in action_map:
        code = action.get("code", "<unknown>")
        if not action.get("primaryAction"):
            errors.append(f"CCSB-T04-DIAGNOSTIC-ACTION: {code} is missing primaryAction.")
        if action.get("targetSurface") not in REQUIRED_SURFACES:
            errors.append(f"CCSB-T04-DIAGNOSTIC-SURFACE: {code} targets an unknown surface.")

    migration = contract.get("migrationActionPanel", {})
    if migration.get("doesNotAutoActivate") is not True:
        errors.append("CCSB-T04-MIGRATION-ACTIVATION: Migration panel must not auto-activate.")
    migration_codes = set(migration.get("visibleWhenAnyDiagnosticCode", []))
    if not {"CCSB-COMPAT-MIGRATION-REQUIRED", "CCSB-COMPAT-MIGRATED-DATA-INVALID"}.issubset(migration_codes):
        errors.append("CCSB-T04-MIGRATION-CODES: Migration action panel must cover migration diagnostics.")
    for action in migration.get("actions", []):
        if action.get("requiresSeparateValidationAfterCompletion") is not True:
            errors.append(f"CCSB-T04-MIGRATION-REVALIDATE: {action.get('id')} must require separate validation.")

    command = contract.get("safeRevalidationCommand", {})
    if command.get("customApi") != "ccsb_ValidateBoardVersion":
        errors.append("CCSB-T04-COMMAND-API: Safe command must call ccsb_ValidateBoardVersion.")
    if "ccsb_ActivateBoardVersion" not in set(command.get("forbiddenCustomApis", [])):
        errors.append("CCSB-T04-COMMAND-FORBIDDEN: Safe command must explicitly forbid activation API.")
    for key in (
        "requiresConfirmation",
        "requiresIdempotencyKey",
        "writesValidationResults",
    ):
        if command.get(key) is not True:
            errors.append(f"CCSB-T04-COMMAND-{key}: Expected true.")
    for key in (
        "mutatesActivePointer",
        "mutatesBoardLifecycle",
        "mutatesPublishState",
        "mutatesScheduleRecords",
    ):
        if command.get(key) is not False:
            errors.append(f"CCSB-T04-COMMAND-{key}: Expected false.")
    if command.get("createsOperationType") != "Validate Board Version":
        errors.append("CCSB-T04-COMMAND-OPERATION: Command must create Validate Board Version operation evidence.")
    for marker in ("boardVersionId", "configurationHash", "targetVersions"):
        if marker not in str(command.get("idempotencyKeyPattern", "")):
            errors.append(f"CCSB-T04-IDEMPOTENCY: Pattern missing {marker}.")
    required_result_fields = {
        "validationRunId",
        "operationId",
        "correlationId",
        "allowed",
        "outcome",
        "compatibilityStatus",
        "diagnostics",
    }
    if required_result_fields - set(command.get("resultFields", [])):
        errors.append("CCSB-T04-COMMAND-RESULT: Result fields are incomplete.")
    if set(command.get("postRunRefreshTargets", [])) - REQUIRED_SURFACES:
        errors.append("CCSB-T04-COMMAND-REFRESH: Command refresh target is unknown.")

    security = contract.get("securityModel", {})
    if "Configuration Administrator" not in set(security.get("canRunSafeValidation", [])):
        errors.append("CCSB-T04-SECURITY: Configuration Administrator must be able to run safe validation.")
    if security.get("activationRemainsSeparatePermission") is not True:
        errors.append("CCSB-T04-SECURITY-ACTIVATION: Activation must remain separately permissioned.")
    if security.get("suppressionRequiresResolutionNote") is not True:
        errors.append("CCSB-T04-SECURITY-SUPPRESSION: Suppression must require a resolution note.")

    gates = set(contract.get("acceptanceGates", []))
    if REQUIRED_GATES - gates:
        errors.append(f"CCSB-T04-GATES: Missing gates {sorted(REQUIRED_GATES - gates)}.")

    return contract, errors, warnings, len(t03_codes)


def write_report(
    path: Path,
    contract_path: Path,
    contract: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    diagnostic_code_count: int,
) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# US-002-T04 Static Administrator Diagnostics Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated}",
        f"**Contract:** `{contract_path.relative_to(ROOT).as_posix()}`",
        "",
        "## Counts",
        "",
        f"- Workspace surfaces: {len(contract.get('workspaceSurfaces', []))}",
        f"- Diagnostic views: {len(contract.get('diagnosticViews', []))}",
        f"- Diagnostic actions: {len(contract.get('diagnosticActionMap', []))}",
        f"- Source T03 diagnostic codes covered: {diagnostic_code_count}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Validation Scope",
        "",
        "- Administrator diagnostics document coverage",
        "- Existing schema field and relationship bindings",
        "- T03 diagnostic catalog action coverage",
        "- Blocking diagnostics, projection health, and operation evidence views",
        "- Safe re-validation command behavior and idempotency",
        "- Migration action visibility without automatic activation",
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
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This report proves the admin diagnostics UX contract and safe command rules. "
            "Provisioning the actual model-driven form, command bar, or PCF surface remains a later connected Dataverse implementation step.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate US-002-T04 administrator diagnostics artifacts.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    contract_path = args.contract.resolve()
    contract, errors, warnings, diagnostic_code_count = validate(contract_path)
    write_report(args.report.resolve(), contract_path, contract, errors, warnings, diagnostic_code_count)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        for issue in errors:
            print(issue)
        return 1
    print(
        f"OK: {len(contract.get('workspaceSurfaces', []))} surfaces, "
        f"{len(contract.get('diagnosticActionMap', []))} diagnostic actions, "
        f"{diagnostic_code_count} source code(s), {len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
