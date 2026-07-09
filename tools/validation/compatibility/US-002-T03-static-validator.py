#!/usr/bin/env python3
"""Static and executable acceptance validator for US-002-T03."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "docs" / "design" / "api-contracts" / "compatibility" / "US-002-T03-preactivation-compatibility-validation.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-002-T03" / "static-report.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
REQUIRED_GROUPS = {
    "T03-RG-001",
    "T03-RG-002",
    "T03-RG-003",
    "T03-RG-004",
    "T03-RG-005",
}
REQUIRED_DIAGNOSTICS = {
    "CCSB-COMPAT-ACTIVATION-BLOCKED",
    "CCSB-COMPAT-EVIDENCE-MISSING",
    "CCSB-COMPAT-CONFIGURATION-INVALID",
    "CCSB-COMPAT-VALIDATION-STALE",
    "CCSB-COMPAT-METADATA-MISSING",
    "CCSB-COMPAT-PRODUCT-UNSUPPORTED",
    "CCSB-COMPAT-SCHEMA-UNSUPPORTED",
    "CCSB-COMPAT-DOWNGRADE-BLOCKED",
    "CCSB-COMPAT-MIGRATION-REQUIRED",
    "CCSB-COMPAT-MIGRATED-DATA-INVALID",
    "CCSB-COMPAT-SOURCE-TYPE-UNSUPPORTED",
    "CCSB-COMPAT-MAPPING-METADATA-STALE",
    "CCSB-COMPAT-MAPPING-REQUIRED-MISSING",
    "CCSB-COMPAT-MAPPING-TYPE-MISMATCH",
    "CCSB-COMPAT-RELATIONSHIP-INCOMPATIBLE",
    "CCSB-COMPAT-FEATURE-FLAG-DISABLED",
    "CCSB-COMPAT-LIVE-SCHEMA-BLOCKED",
    "CCSB-COMPAT-PROJECTION-STALE",
    "CCSB-COMPAT-PROJECTION-METADATA-MISMATCH",
}
REQUIRED_GATES = {
    "all-five-rule-groups-evaluated",
    "configuration-and-mappings-validated",
    "required-feature-flags-validated",
    "migrated-data-evidence-validated",
    "runtime-projection-validated",
    "machine-readable-diagnostics-returned",
    "every-diagnostic-has-remediation-link",
    "activation-fails-closed-without-pointer-mutation",
    "validation-results-persisted",
    "stale-validation-rejected",
    "reference-fixtures-pass",
    "static-validator-pass",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def linked_path(contract: dict[str, Any], key: str, errors: list[str]) -> Path | None:
    value = contract.get(key)
    if not isinstance(value, str):
        errors.append(f"CCSB-T03-LINK: {key} must be a repository-relative path.")
        return None
    path = ROOT / value
    if not path.exists():
        errors.append(f"CCSB-T03-LINK-MISSING: {key} does not exist: {value}.")
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


def load_engine(path: Path) -> Any:
    spec = importlib.util.spec_from_file_location("ccsb_t03_engine", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load reference implementation: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate(
    contract_path: Path,
) -> tuple[dict[str, Any], list[str], list[str], int, set[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    fixture_count = 0
    fixture_codes: set[str] = set()
    contract = read_json(contract_path)

    if contract.get("task") != "US-002-T03":
        errors.append("CCSB-T03-TASK-ID: Contract task must be US-002-T03.")
    if not isinstance(contract.get("manifestVersion"), str) or not SEMVER.match(contract["manifestVersion"]):
        errors.append("CCSB-T03-MANIFEST-VERSION: manifestVersion must be semantic version x.y.z.")

    document_path = linked_path(contract, "validationDocument", errors)
    engine_path = linked_path(contract, "referenceImplementation", errors)
    fixtures_path = linked_path(contract, "validationFixtures", errors)
    t01_path = linked_path(contract, "sourceCompatibilityContract", errors)
    t02_path = linked_path(contract, "sourceMetadataContract", errors)
    t10_path = linked_path(contract, "sourceUpgradeManifest", errors)
    schema_path = linked_path(contract, "sourceSchema", errors)

    if document_path:
        document = document_path.read_text(encoding="utf-8-sig")
        for heading in (
            "Runtime Boundary",
            "Configuration and Evidence",
            "Version and Migration Validation",
            "Mapping Validation",
            "Feature Flags and Live Schema",
            "Runtime Projection Validation",
            "Stale Validation Protection",
            "Activation Denial",
            "Persistence",
            "Verification",
        ):
            if f"## {heading}" not in document:
                errors.append(f"CCSB-T03-DOCUMENT-COVERAGE: Missing heading: {heading}.")

    target = contract.get("targetVersions", {})
    expected_target = {
        "productSemanticVersion": "1.0.0",
        "foundationSolutionVersion": "1.0.0.1",
        "configurationSchemaVersion": "1.0.0",
        "runtimeProjectionSchemaVersion": "1.0.0",
    }
    if target != expected_target:
        errors.append("CCSB-T03-TARGET-VERSIONS: targetVersions must declare the approved V1 line.")
    for key, value in target.items():
        if key == "foundationSolutionVersion":
            if not re.match(r"^\d+\.\d+\.\d+\.\d+$", str(value)):
                errors.append(f"CCSB-T03-TARGET-VERSION-FORMAT: {key} is invalid.")
        elif not SEMVER.match(str(value)):
            errors.append(f"CCSB-T03-TARGET-VERSION-FORMAT: {key} is invalid.")

    if t01_path:
        t01 = read_json(t01_path)
        dimensions = t01.get("versionDimensions", {})
        for key, value in expected_target.items():
            if dimensions.get(key) != value:
                errors.append(f"CCSB-T03-T01-VERSION: {key} does not match T01.")
        t01_codes = {item.get("code") for item in t01.get("diagnosticCodes", [])}
        contract_codes = {item.get("code") for item in contract.get("diagnosticCatalog", [])}
        if not t01_codes.issubset(contract_codes):
            errors.append(
                f"CCSB-T03-T01-DIAGNOSTICS: Missing T01 codes {sorted(t01_codes - contract_codes)}."
            )
    if t02_path:
        t02 = read_json(t02_path)
        t02_codes = {item.get("code") for item in t02.get("diagnosticCodes", [])}
        contract_codes = {item.get("code") for item in contract.get("diagnosticCatalog", [])}
        if not t02_codes.issubset(contract_codes):
            errors.append(
                f"CCSB-T03-T02-DIAGNOSTICS: Missing T02 codes {sorted(t02_codes - contract_codes)}."
            )
    if t10_path:
        t10 = read_json(t10_path)
        known_flags = {
            item.get("key") for item in t10.get("changePolicy", {}).get("featureFlags", [])
        }
        required_flags = set(contract.get("requiredFeatureFlags", []))
        if not required_flags.issubset(known_flags):
            errors.append(
                f"CCSB-T03-FEATURE-FLAGS: Unknown flags {sorted(required_flags - known_flags)}."
            )

    policy = contract.get("evaluation", {})
    if policy.get("failClosed") is not True or policy.get("missingInputIsBlocking") is not True:
        errors.append("CCSB-T03-FAIL-CLOSED: Missing input and blocking diagnostics must fail closed.")
    if set(policy.get("blockOnSeverities", [])) != {"blocking", "error"}:
        errors.append("CCSB-T03-SEVERITIES: blockOnSeverities must contain blocking and error.")
    if set(policy.get("eligibleLifecycleStates", [])) != {"Ready"}:
        errors.append("CCSB-T03-LIFECYCLE: Only Ready board versions are activation eligible.")
    if set(policy.get("allowedMigrationStates", [])) != {"None", "Completed"}:
        errors.append("CCSB-T03-MIGRATION-STATES: Only None and Completed are activation eligible.")

    groups = contract.get("validationRuleGroups", [])
    group_ids = {group.get("id") for group in groups}
    if group_ids != REQUIRED_GROUPS:
        errors.append(
            f"CCSB-T03-RULE-GROUPS: Rule groups missing={sorted(REQUIRED_GROUPS - group_ids)} "
            f"unexpected={sorted(group_ids - REQUIRED_GROUPS)}."
        )
    rule_codes: set[str] = set()
    rule_ids: set[str] = set()
    for group in groups:
        if group.get("required") is not True:
            errors.append(f"CCSB-T03-RULE-GROUP-REQUIRED: {group.get('id')} must be required.")
        rules = group.get("rules", [])
        if not rules:
            errors.append(f"CCSB-T03-RULE-GROUP-EMPTY: {group.get('id')} has no rules.")
        for rule in rules:
            rule_id = rule.get("id")
            if not isinstance(rule_id, str) or rule_id in rule_ids:
                errors.append(f"CCSB-T03-RULE-ID: Invalid or duplicate rule ID {rule_id}.")
            else:
                rule_ids.add(rule_id)
            codes = rule.get("diagnosticCodes", [])
            if not codes:
                errors.append(f"CCSB-T03-RULE-DIAGNOSTICS: {rule_id} has no diagnostics.")
            rule_codes.update(codes)

    catalog = contract.get("diagnosticCatalog", [])
    catalog_codes = {item.get("code") for item in catalog}
    if REQUIRED_DIAGNOSTICS - catalog_codes:
        errors.append(
            f"CCSB-T03-DIAGNOSTICS: Missing codes {sorted(REQUIRED_DIAGNOSTICS - catalog_codes)}."
        )
    if rule_codes - catalog_codes:
        errors.append(
            f"CCSB-T03-RULE-CATALOG: Rules reference unknown codes {sorted(rule_codes - catalog_codes)}."
        )
    for diagnostic in catalog:
        code = diagnostic.get("code", "<unknown>")
        if diagnostic.get("severity") not in {"blocking", "error", "warning"}:
            errors.append(f"CCSB-T03-DIAGNOSTIC-SEVERITY: {code} has an invalid severity.")
        for key in ("category", "message", "recommendedAction", "remediationLink"):
            if not diagnostic.get(key):
                errors.append(f"CCSB-T03-DIAGNOSTIC-FIELD: {code} is missing {key}.")
        remediation = diagnostic.get("remediationLink")
        if isinstance(remediation, str):
            file_value = remediation.split("#", 1)[0]
            if not (ROOT / file_value).exists():
                errors.append(f"CCSB-T03-REMEDIATION-LINK: {code} points to a missing document.")

    integration = contract.get("activationIntegration", {})
    if integration.get("validationConsumer") != "ccsb_ValidateBoardVersion":
        errors.append("CCSB-T03-VALIDATION-CONSUMER: Validation consumer is incorrect.")
    if integration.get("activationConsumer") != "ccsb_ActivateBoardVersion":
        errors.append("CCSB-T03-ACTIVATION-CONSUMER: Activation consumer is incorrect.")
    denial = integration.get("denialBehavior", {})
    if (
        denial.get("customApiSucceeded") is not False
        or denial.get("activePointerMutated") is not False
        or denial.get("boardLifecycleMutated") is not False
        or denial.get("diagnosticsPersisted") is not True
        or denial.get("primaryErrorCode") != "CCSB-COMPAT-ACTIVATION-BLOCKED"
    ):
        errors.append("CCSB-T03-DENIAL: Activation denial must retain evidence and mutate no pointers.")
    stale_rule = integration.get("staleValidationRule", "")
    for marker in ("boardVersionId", "configurationHash", "targetVersions", "evidenceFingerprint"):
        if marker not in stale_rule:
            errors.append(f"CCSB-T03-STALE-TOKEN: staleValidationRule is missing {marker}.")

    required_result_fields = {
        "validationRunId",
        "boardVersionId",
        "configurationHash",
        "targetVersions",
        "evidenceFingerprint",
        "allowed",
        "outcome",
        "compatibilityStatus",
        "diagnostics",
    }
    if required_result_fields - set(contract.get("resultContract", {}).get("requiredFields", [])):
        errors.append("CCSB-T03-RESULT-CONTRACT: Result contract is incomplete.")

    if schema_path:
        schema = read_json(schema_path)
        for binding_name, binding in contract.get("persistenceBindings", {}).items():
            entity = binding.get("entity")
            available = schema_fields(schema, entity)
            missing_fields = set(binding.get("fields", [])) - available
            if missing_fields:
                errors.append(
                    f"CCSB-T03-PERSISTENCE: {binding_name}/{entity} missing fields {sorted(missing_fields)}."
                )

    if engine_path and fixtures_path:
        try:
            engine = load_engine(engine_path)
            fixture_count, fixture_failures = engine.run_self_test(contract_path, fixtures_path)
            for failure in fixture_failures:
                errors.append(f"CCSB-T03-FIXTURE: {failure}")
            fixtures = read_json(fixtures_path)
            for case in fixtures.get("cases", []):
                result = engine.evaluate(case["snapshot"], contract)
                fixture_codes.update(item["code"] for item in result.get("diagnostics", []))
        except Exception as exc:  # pragma: no cover - defensive validator boundary
            errors.append(f"CCSB-T03-ENGINE: Reference implementation failed: {exc}")
    if fixture_count < 2:
        errors.append("CCSB-T03-FIXTURE-COUNT: At least pass and block fixtures are required.")
    exercised_required = REQUIRED_DIAGNOSTICS - {"CCSB-COMPAT-ACTIVATION-BLOCKED"}
    if exercised_required - fixture_codes:
        errors.append(
            f"CCSB-T03-FIXTURE-COVERAGE: Unexercised codes {sorted(exercised_required - fixture_codes)}."
        )

    gates = set(contract.get("acceptanceGates", []))
    if REQUIRED_GATES - gates:
        errors.append(f"CCSB-T03-GATES: Missing gates {sorted(REQUIRED_GATES - gates)}.")
    return contract, errors, warnings, fixture_count, fixture_codes


def write_report(
    path: Path,
    contract_path: Path,
    contract: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    fixture_count: int,
    fixture_codes: set[str],
) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# US-002-T03 Static Pre-Activation Validation Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated}",
        f"**Contract:** `{contract_path.relative_to(ROOT).as_posix()}`",
        "",
        "## Counts",
        "",
        f"- Rule groups: {len(contract.get('validationRuleGroups', []))}",
        f"- Diagnostic codes: {len(contract.get('diagnosticCatalog', []))}",
        f"- Executed fixtures: {fixture_count}",
        f"- Diagnostic codes exercised: {len(fixture_codes)}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Validation Scope",
        "",
        "- T01/T02 version, diagnostic, and persistence continuity",
        "- T10 required feature-flag continuity",
        "- All configuration, mapping, migration, schema, flag, and projection rule groups",
        "- Machine-readable diagnostic and remediation-link completeness",
        "- Activation denial, stale-token, and no-pointer-mutation policy",
        "- Executable compatible and incompatible snapshot fixtures",
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
            "This report proves the executable validation core and its Dataverse integration contract. "
            "Connected Custom API registration and live activation execution require the future board runtime plug-in package.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate US-002-T03 artifacts.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    contract_path = args.contract.resolve()
    contract, errors, warnings, fixture_count, fixture_codes = validate(contract_path)
    write_report(
        args.report.resolve(),
        contract_path,
        contract,
        errors,
        warnings,
        fixture_count,
        fixture_codes,
    )
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        for issue in errors:
            print(issue)
        return 1
    print(
        f"OK: {len(contract.get('validationRuleGroups', []))} rule groups, "
        f"{len(contract.get('diagnosticCatalog', []))} diagnostics, "
        f"{fixture_count} fixture(s), {len(warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
