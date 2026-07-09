#!/usr/bin/env python3
"""Executable reference engine for US-002-T03 pre-activation validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "docs" / "design" / "api-contracts" / "compatibility" / "US-002-T03-preactivation-compatibility-validation.json"
DEFAULT_FIXTURES = ROOT / "tests" / "Fixtures" / "Compatibility" / "US-002-T03-validation-fixtures.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def canonical_fingerprint(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def version_tuple(value: Any) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    parts = value.split(".")
    if len(parts) != 3 or any(not part.isdigit() for part in parts):
        return None
    return tuple(int(part) for part in parts)  # type: ignore[return-value]


def evaluate(snapshot: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
    catalog = {item["code"]: item for item in contract["diagnosticCatalog"]}
    target = contract["targetVersions"]
    policy = contract["evaluation"]
    evidence_fingerprint = canonical_fingerprint(snapshot)
    diagnostics: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(
        code: str,
        rule_id: str,
        *,
        affected_record_id: Any = None,
        affected_field: Any = None,
        expected: Any = None,
        actual: Any = None,
    ) -> None:
        record = "" if affected_record_id is None else str(affected_record_id)
        field = "" if affected_field is None else str(affected_field)
        key = (code, record, field)
        if key in seen:
            return
        seen.add(key)
        definition = catalog[code]
        diagnostics.append(
            {
                "code": code,
                "severity": definition["severity"],
                "category": definition["category"],
                "message": definition["message"],
                "recommendedAction": definition["recommendedAction"],
                "remediationLink": definition["remediationLink"],
                "affectedRecordId": affected_record_id,
                "affectedField": affected_field,
                "detail": {
                    "ruleId": rule_id,
                    "expected": expected,
                    "actual": actual,
                    "targetVersions": target,
                    "evidenceFingerprint": evidence_fingerprint,
                },
            }
        )

    board = snapshot.get("boardVersion")
    if not isinstance(board, dict):
        board = {}
        add(
            "CCSB-COMPAT-EVIDENCE-MISSING",
            "CCSB-T03-REQUEST-COMPLETE",
            expected="boardVersion object",
            actual=snapshot.get("boardVersion"),
        )

    board_id = board.get("id")
    configuration_hash = board.get("configurationHash")
    for field_name in ("id", "rowVersion", "configurationHash", "sourceChangeToken"):
        if not board.get(field_name):
            add(
                "CCSB-COMPAT-EVIDENCE-MISSING",
                "CCSB-T03-REQUEST-COMPLETE",
                affected_record_id=board_id,
                affected_field=field_name,
                expected="non-empty value",
                actual=board.get(field_name),
            )
    if board.get("lifecycleState") not in policy["eligibleLifecycleStates"]:
        add(
            "CCSB-COMPAT-CONFIGURATION-INVALID",
            "CCSB-T03-REQUEST-COMPLETE",
            affected_record_id=board_id,
            affected_field="ccsb_lifecyclestate",
            expected=policy["eligibleLifecycleStates"],
            actual=board.get("lifecycleState"),
        )

    checks = snapshot.get("configurationChecks")
    if not isinstance(checks, list):
        checks = []
        add(
            "CCSB-COMPAT-EVIDENCE-MISSING",
            "CCSB-T03-CONFIGURATION-CHECKS",
            affected_record_id=board_id,
            expected="configurationChecks array",
            actual=snapshot.get("configurationChecks"),
        )
    check_by_id = {item.get("id"): item for item in checks if isinstance(item, dict)}
    for check_id in contract["requiredConfigurationChecks"]:
        check = check_by_id.get(check_id)
        if not check:
            add(
                "CCSB-COMPAT-EVIDENCE-MISSING",
                "CCSB-T03-CONFIGURATION-CHECKS",
                affected_record_id=check_id,
                expected="required check",
                actual="missing",
            )
            continue
        status = str(check.get("status", "")).lower()
        if status in {"block", "error", "fail", "failed", "invalid"}:
            add(
                "CCSB-COMPAT-CONFIGURATION-INVALID",
                "CCSB-T03-CONFIGURATION-CHECKS",
                affected_record_id=check.get("affectedRecordId") or check_id,
                affected_field=check.get("affectedField"),
                expected="pass or warning",
                actual=status,
            )
        elif status not in {"pass", "warn", "warning"}:
            add(
                "CCSB-COMPAT-EVIDENCE-MISSING",
                "CCSB-T03-CONFIGURATION-CHECKS",
                affected_record_id=check_id,
                expected="pass, warning, or block",
                actual=check.get("status"),
            )
        if check.get("configurationHash") != configuration_hash:
            add(
                "CCSB-COMPAT-VALIDATION-STALE",
                "CCSB-T03-CONFIGURATION-CHECKS",
                affected_record_id=check_id,
                affected_field="configurationHash",
                expected=configuration_hash,
                actual=check.get("configurationHash"),
            )

    product_version = board.get("productVersion")
    configuration_schema = board.get("configurationSchemaVersion")
    migration_state = board.get("migrationState")
    for field_name, value in (
        ("ccsb_productversion", product_version),
        ("ccsb_configurationschemaversion", configuration_schema),
        ("ccsb_migrationstate", migration_state),
    ):
        if value in (None, ""):
            add(
                "CCSB-COMPAT-METADATA-MISSING",
                "CCSB-T03-VERSION-METADATA",
                affected_record_id=board_id,
                affected_field=field_name,
                expected="non-empty compatibility metadata",
                actual=value,
            )

    if product_version != target["productSemanticVersion"]:
        add(
            "CCSB-COMPAT-PRODUCT-UNSUPPORTED",
            "CCSB-T03-VERSION-METADATA",
            affected_record_id=board_id,
            affected_field="ccsb_productversion",
            expected=target["productSemanticVersion"],
            actual=product_version,
        )
    product_tuple = version_tuple(product_version)
    product_target_tuple = version_tuple(target["productSemanticVersion"])
    if product_tuple and product_target_tuple and product_tuple > product_target_tuple:
        add(
            "CCSB-COMPAT-DOWNGRADE-BLOCKED",
            "CCSB-T03-VERSION-METADATA",
            affected_record_id=board_id,
            affected_field="ccsb_productversion",
            expected=f"less than or equal to {target['productSemanticVersion']}",
            actual=product_version,
        )
    if configuration_schema != target["configurationSchemaVersion"]:
        add(
            "CCSB-COMPAT-SCHEMA-UNSUPPORTED",
            "CCSB-T03-VERSION-METADATA",
            affected_record_id=board_id,
            affected_field="ccsb_configurationschemaversion",
            expected=target["configurationSchemaVersion"],
            actual=configuration_schema,
        )
    schema_tuple = version_tuple(configuration_schema)
    schema_target_tuple = version_tuple(target["configurationSchemaVersion"])
    if schema_tuple and schema_target_tuple and schema_tuple > schema_target_tuple:
        add(
            "CCSB-COMPAT-DOWNGRADE-BLOCKED",
            "CCSB-T03-VERSION-METADATA",
            affected_record_id=board_id,
            affected_field="ccsb_configurationschemaversion",
            expected=f"less than or equal to {target['configurationSchemaVersion']}",
            actual=configuration_schema,
        )

    if migration_state not in policy["allowedMigrationStates"]:
        add(
            "CCSB-COMPAT-MIGRATION-REQUIRED",
            "CCSB-T03-MIGRATION-STATE",
            affected_record_id=board_id,
            affected_field="ccsb_migrationstate",
            expected=policy["allowedMigrationStates"],
            actual=migration_state,
        )
    migration_checks = snapshot.get("migrationDataChecks")
    if not isinstance(migration_checks, list):
        migration_checks = []
    migration_by_id = {item.get("id"): item for item in migration_checks if isinstance(item, dict)}
    for check_id in contract["requiredMigrationDataChecks"]:
        check = migration_by_id.get(check_id)
        if not check:
            add(
                "CCSB-COMPAT-EVIDENCE-MISSING",
                "CCSB-T03-MIGRATION-STATE",
                affected_record_id=check_id,
                expected="required migrated-data check",
                actual="missing",
            )
        elif str(check.get("status", "")).lower() != "pass":
            add(
                "CCSB-COMPAT-MIGRATED-DATA-INVALID",
                "CCSB-T03-MIGRATION-STATE",
                affected_record_id=check.get("affectedRecordId") or check_id,
                expected="pass",
                actual=check.get("status"),
            )

    entity_definitions = snapshot.get("entityDefinitions")
    if not isinstance(entity_definitions, list):
        entity_definitions = []
        add(
            "CCSB-COMPAT-EVIDENCE-MISSING",
            "CCSB-T03-ENTITY-DEFINITIONS",
            expected="entityDefinitions array",
            actual=snapshot.get("entityDefinitions"),
        )
    for entity in entity_definitions:
        if not isinstance(entity, dict) or not entity.get("enabled"):
            continue
        if entity.get("sourceType") not in policy["supportedSourceTypes"]:
            add(
                "CCSB-COMPAT-SOURCE-TYPE-UNSUPPORTED",
                "CCSB-T03-ENTITY-DEFINITIONS",
                affected_record_id=entity.get("id"),
                affected_field="ccsb_sourcetype",
                expected=policy["supportedSourceTypes"],
                actual=entity.get("sourceType"),
            )
        if entity.get("validationStatus") != "Valid" or entity.get("metadataCurrent") is not True:
            add(
                "CCSB-COMPAT-MAPPING-METADATA-STALE",
                "CCSB-T03-ENTITY-DEFINITIONS",
                affected_record_id=entity.get("id"),
                expected={"validationStatus": "Valid", "metadataCurrent": True},
                actual={
                    "validationStatus": entity.get("validationStatus"),
                    "metadataCurrent": entity.get("metadataCurrent"),
                },
            )

    field_mappings = snapshot.get("fieldMappings")
    if not isinstance(field_mappings, list):
        field_mappings = []
        add(
            "CCSB-COMPAT-EVIDENCE-MISSING",
            "CCSB-T03-FIELD-MAPPINGS",
            expected="fieldMappings array",
            actual=snapshot.get("fieldMappings"),
        )
    for mapping in field_mappings:
        if not isinstance(mapping, dict) or not mapping.get("enabled"):
            continue
        if mapping.get("required") and mapping.get("resolved") is not True:
            add(
                "CCSB-COMPAT-MAPPING-REQUIRED-MISSING",
                "CCSB-T03-FIELD-MAPPINGS",
                affected_record_id=mapping.get("id"),
                affected_field=mapping.get("affectedField"),
                expected=True,
                actual=mapping.get("resolved"),
            )
        if mapping.get("resolved") is True and mapping.get("typeCompatible") is not True:
            add(
                "CCSB-COMPAT-MAPPING-TYPE-MISMATCH",
                "CCSB-T03-FIELD-MAPPINGS",
                affected_record_id=mapping.get("id"),
                affected_field=mapping.get("affectedField"),
                expected=True,
                actual=mapping.get("typeCompatible"),
            )

    relationship_mappings = snapshot.get("relationshipMappings")
    if not isinstance(relationship_mappings, list):
        relationship_mappings = []
        add(
            "CCSB-COMPAT-EVIDENCE-MISSING",
            "CCSB-T03-RELATIONSHIP-MAPPINGS",
            expected="relationshipMappings array",
            actual=snapshot.get("relationshipMappings"),
        )
    for mapping in relationship_mappings:
        if not isinstance(mapping, dict) or not mapping.get("enabled"):
            continue
        if mapping.get("required") and (
            mapping.get("resolved") is not True or mapping.get("metadataCompatible") is not True
        ):
            add(
                "CCSB-COMPAT-RELATIONSHIP-INCOMPATIBLE",
                "CCSB-T03-RELATIONSHIP-MAPPINGS",
                affected_record_id=mapping.get("id"),
                expected={"resolved": True, "metadataCompatible": True},
                actual={
                    "resolved": mapping.get("resolved"),
                    "metadataCompatible": mapping.get("metadataCompatible"),
                },
            )

    flags = snapshot.get("featureFlags")
    if not isinstance(flags, dict):
        flags = {}
    for flag in contract["requiredFeatureFlags"]:
        if flags.get(flag) is not True:
            add(
                "CCSB-COMPAT-FEATURE-FLAG-DISABLED",
                "CCSB-T03-FEATURE-FLAGS",
                affected_record_id=flag,
                expected=True,
                actual=flags.get(flag),
            )

    live_report = snapshot.get("liveSchemaReport")
    if not isinstance(live_report, dict):
        live_report = {}
    live_schema_valid = (
        live_report.get("present") is True
        and live_report.get("current") is True
        and live_report.get("solutionVersion") == target["foundationSolutionVersion"]
        and live_report.get("blockerCount") == 0
    )
    if not live_schema_valid:
        add(
            "CCSB-COMPAT-LIVE-SCHEMA-BLOCKED",
            "CCSB-T03-LIVE-SCHEMA",
            expected={
                "present": True,
                "current": True,
                "solutionVersion": target["foundationSolutionVersion"],
                "blockerCount": 0,
            },
            actual=live_report,
        )

    projection = snapshot.get("runtimeProjection")
    if not isinstance(projection, dict):
        projection = {}
    projection_current = (
        bool(projection)
        and projection.get("isCurrent") is True
        and projection.get("status") in policy["allowedProjectionStatuses"]
        and projection.get("projectionSchemaVersion") == target["runtimeProjectionSchemaVersion"]
        and projection.get("configurationHash") == configuration_hash
        and projection.get("sourceChangeToken") == board.get("sourceChangeToken")
    )
    if not projection_current:
        add(
            "CCSB-COMPAT-PROJECTION-STALE",
            "CCSB-T03-PROJECTION-CURRENT",
            affected_record_id=projection.get("id"),
            expected={
                "isCurrent": True,
                "status": policy["allowedProjectionStatuses"],
                "projectionSchemaVersion": target["runtimeProjectionSchemaVersion"],
                "configurationHash": configuration_hash,
                "sourceChangeToken": board.get("sourceChangeToken"),
            },
            actual=projection,
        )
    projection_metadata_matches = (
        bool(projection)
        and projection.get("productVersion") == product_version
        and projection.get("configurationSchemaVersion") == configuration_schema
    )
    if not projection_metadata_matches:
        add(
            "CCSB-COMPAT-PROJECTION-METADATA-MISMATCH",
            "CCSB-T03-PROJECTION-CURRENT",
            affected_record_id=projection.get("id"),
            expected={
                "productVersion": product_version,
                "configurationSchemaVersion": configuration_schema,
            },
            actual={
                "productVersion": projection.get("productVersion"),
                "configurationSchemaVersion": projection.get("configurationSchemaVersion"),
            },
        )

    blocking_severities = set(policy["blockOnSeverities"])
    allowed = not any(item["severity"] in blocking_severities for item in diagnostics)
    has_warning = any(
        str(check.get("status", "")).lower() in {"warn", "warning"}
        for check in checks
        if isinstance(check, dict)
    )
    outcome = "Pass" if allowed and not has_warning else "Warning" if allowed else "Block"
    compatibility_status = (
        "Compatible"
        if outcome == "Pass"
        else "Compatible With Warnings"
        if outcome == "Warning"
        else "Incompatible"
    )
    return {
        "validationRunId": snapshot.get("validationRunId"),
        "boardVersionId": board_id,
        "configurationHash": configuration_hash,
        "targetVersions": target,
        "evidenceFingerprint": evidence_fingerprint,
        "allowed": allowed,
        "outcome": outcome,
        "compatibilityStatus": compatibility_status,
        "primaryErrorCode": None if allowed else "CCSB-COMPAT-ACTIVATION-BLOCKED",
        "diagnostics": diagnostics,
    }


def run_self_test(contract_path: Path, fixtures_path: Path) -> tuple[int, list[str]]:
    contract = read_json(contract_path)
    fixtures = read_json(fixtures_path)
    failures: list[str] = []
    for case in fixtures.get("cases", []):
        result = evaluate(case["snapshot"], contract)
        expected = case["expected"]
        for field in ("allowed", "outcome", "compatibilityStatus"):
            if result.get(field) != expected.get(field):
                failures.append(
                    f"{case['id']}: {field} expected {expected.get(field)!r}, got {result.get(field)!r}"
                )
        actual_codes = {item["code"] for item in result["diagnostics"]}
        expected_codes = set(expected.get("diagnosticCodes", []))
        if actual_codes != expected_codes:
            failures.append(
                f"{case['id']}: diagnostic codes missing={sorted(expected_codes - actual_codes)} "
                f"unexpected={sorted(actual_codes - expected_codes)}"
            )
        for diagnostic in result["diagnostics"]:
            if not diagnostic.get("remediationLink"):
                failures.append(f"{case['id']}: {diagnostic.get('code')} has no remediation link")
    return len(fixtures.get("cases", [])), failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a US-002-T03 compatibility snapshot.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--snapshot", type=Path)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    contract_path = args.contract.resolve()
    if args.self_test:
        count, failures = run_self_test(contract_path, args.fixtures.resolve())
        if failures:
            print(f"FAIL: {len(failures)} assertion(s) across {count} fixture(s).")
            for failure in failures:
                print(failure)
            return 1
        print(f"OK: {count} fixture(s) passed.")
        return 0
    if not args.snapshot:
        parser.error("--snapshot is required unless --self-test is used")

    result = evaluate(read_json(args.snapshot.resolve()), read_json(contract_path))
    payload = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.resolve().write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    return 0 if result["allowed"] else 2


if __name__ == "__main__":
    sys.exit(main())
