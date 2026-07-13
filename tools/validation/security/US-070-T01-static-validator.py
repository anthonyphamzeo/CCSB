#!/usr/bin/env python3
"""Static acceptance validator for US-070-T01."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_MATRIX = ROOT / "tests" / "Fixtures" / "Security" / "US-070-T01-permission-matrix.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-070-T01" / "static-report.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")

REQUIRED_PERSONAS = {"admin", "scheduler", "publisher", "support", "unauthorised"}
REQUIRED_FLAGS = {
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
REQUIRED_SCOPE_DIMENSIONS = {"board", "boardVersion", "location", "group", "resource", "timeWindow", "fieldPolicy"}
REQUIRED_PRINCIPLES = {
    "dataverse-security-first",
    "ccsb-permissions-only-restrict",
    "server-resolved-identity-and-scope",
    "custom-api-only-mutations",
    "fail-closed-on-missing-or-stale-security-input",
    "least-disclosure-denials",
}
REQUIRED_EVALUATION_STEPS = [
    "resolve-platform-caller",
    "dataverse-table-row-privilege",
    "dataverse-field-security",
    "ccsb-profile-flag",
    "ccsb-assignment-scope",
    "command-policy",
    "redacted-decision",
]
REQUIRED_NEGATIVE_CATEGORIES = {
    "no-dataverse-privilege",
    "field-security-denied",
    "missing-ccsb-profile",
    "disabled-or-expired-assignment",
    "out-of-scope-board",
    "forged-payload-scope",
    "publish-denied",
    "rollback-denied",
    "support-raw-payload-request",
    "direct-client-mutation",
    "unauthorised-persona-denied",
}
REQUIRED_DIAGNOSTICS = {
    "CCSB-SEC-DATAVERSE-DENIED",
    "CCSB-SEC-FIELD-REDACTED",
    "CCSB-SEC-PROFILE-MISSING",
    "CCSB-SEC-ASSIGNMENT-INACTIVE",
    "CCSB-SEC-SCOPE-DENIED",
    "CCSB-SEC-FORGED-SCOPE",
    "CCSB-SEC-ACTION-DENIED",
    "CCSB-SEC-DIRECT-MUTATION-DENIED",
}
REQUIRED_GATES = {
    "admin-scheduler-publisher-support-unauthorised-personas-defined",
    "all-profile-flags-mapped-to-actions",
    "dataverse-prerequisites-defined-for-every-action",
    "ccsb-permissions-only-restrict-dataverse-access",
    "direct-client-mutation-denied-for-mutating-actions",
    "negative-cases-cover-dataverse-field-scope-forgery-publish-rollback-support-and-direct-mutation",
    "least-disclosure-denials-required",
    "matrix-feeds-us-070-t03-and-us-070-t05",
}
REQUIRED_DOC_HEADINGS = {
    "Purpose",
    "Security Principles",
    "Evaluation Order",
    "Personas",
    "CCSB Action Catalog",
    "Scope Dimensions",
    "Dataverse Security Relationship",
    "Required Negative Cases",
    "Server Contract for US-070-T03",
    "Testing Contract for US-070-T05",
    "Verification",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def linked_path(matrix: dict[str, Any], key: str, errors: list[str]) -> Path | None:
    value = matrix.get(key)
    if not isinstance(value, str):
        errors.append(f"CCSB-T01-LINK: {key} must be a repository-relative path.")
        return None
    path = ROOT / value
    if not path.exists():
        errors.append(f"CCSB-T01-LINK-MISSING: {key} does not exist: {value}.")
        return None
    return path


def validate(matrix_path: Path) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    matrix = read_json(matrix_path)

    if matrix.get("task") != "US-070-T01":
        errors.append("CCSB-T01-TASK-ID: Matrix task must be US-070-T01.")
    for key in ("manifestVersion", "policyVersion"):
        value = matrix.get(key)
        if not isinstance(value, str) or not SEMVER.match(value):
            errors.append(f"CCSB-T01-VERSION: {key} must be semantic version x.y.z.")

    design_path = linked_path(matrix, "designDocument", errors)
    if design_path:
        document = design_path.read_text(encoding="utf-8-sig")
        for heading in sorted(REQUIRED_DOC_HEADINGS):
            if f"## {heading}" not in document:
                errors.append(f"CCSB-T01-DOC-HEADING: Missing heading: {heading}.")
        for marker in ("CCSB permissions never grant access", "Dataverse is the outer authorization boundary"):
            if marker not in document:
                errors.append(f"CCSB-T01-DOC-POLICY: Missing policy marker: {marker}.")

    for evidence in matrix.get("sourceEvidence", []):
        if not isinstance(evidence, str) or not (ROOT / evidence).exists():
            errors.append(f"CCSB-T01-EVIDENCE-LINK: Missing source evidence path: {evidence}.")

    principles = set(matrix.get("permissionPrinciples", []))
    if REQUIRED_PRINCIPLES - principles:
        errors.append(f"CCSB-T01-PRINCIPLES: Missing principles {sorted(REQUIRED_PRINCIPLES - principles)}.")
    if matrix.get("evaluationOrder") != REQUIRED_EVALUATION_STEPS:
        errors.append("CCSB-T01-EVALUATION-ORDER: Evaluation order must enforce Dataverse before CCSB profile and scope.")

    personas = matrix.get("personas", [])
    persona_ids = {persona.get("id") for persona in personas}
    if persona_ids != REQUIRED_PERSONAS:
        errors.append(f"CCSB-T01-PERSONAS: missing={sorted(REQUIRED_PERSONAS - persona_ids)} unexpected={sorted(persona_ids - REQUIRED_PERSONAS)}.")
    for persona in personas:
        persona_id = persona.get("id", "<unknown>")
        flags = persona.get("defaultProfileFlags", {})
        missing_flags = REQUIRED_FLAGS - set(flags)
        unexpected_flags = set(flags) - REQUIRED_FLAGS
        if missing_flags or unexpected_flags:
            errors.append(f"CCSB-T01-PERSONA-FLAGS: {persona_id} missing={sorted(missing_flags)} unexpected={sorted(unexpected_flags)}.")
        if persona_id == "unauthorised" and any(flags.values()):
            errors.append("CCSB-T01-UNAUTHORISED-FLAGS: Unauthorised persona must have no true profile flags.")

    scope_dimensions = {item.get("id") for item in matrix.get("scopeDimensions", [])}
    if REQUIRED_SCOPE_DIMENSIONS - scope_dimensions:
        errors.append(f"CCSB-T01-SCOPE-DIMENSIONS: Missing dimensions {sorted(REQUIRED_SCOPE_DIMENSIONS - scope_dimensions)}.")

    actions = matrix.get("actions", [])
    action_ids: set[str] = set()
    flags_covered: set[str] = set()
    mutating_actions = 0
    for action in actions:
        action_id = action.get("id")
        if not isinstance(action_id, str) or not action_id:
            errors.append("CCSB-T01-ACTION-ID: Every action requires an id.")
            continue
        if action_id in action_ids:
            errors.append(f"CCSB-T01-ACTION-DUPLICATE: Duplicate action id {action_id}.")
        action_ids.add(action_id)
        flag = action.get("profileFlag")
        if flag not in REQUIRED_FLAGS:
            errors.append(f"CCSB-T01-ACTION-FLAG: {action_id} has invalid profileFlag {flag}.")
        else:
            flags_covered.add(flag)
        allowed = set(action.get("allowedPersonas", []))
        denied = set(action.get("deniedPersonas", []))
        if not allowed:
            errors.append(f"CCSB-T01-ACTION-ALLOW: {action_id} must allow at least one persona.")
        if allowed - REQUIRED_PERSONAS or denied - REQUIRED_PERSONAS:
            errors.append(f"CCSB-T01-ACTION-PERSONA: {action_id} references an unknown persona.")
        if allowed & denied:
            errors.append(f"CCSB-T01-ACTION-CONFLICT: {action_id} both allows and denies {sorted(allowed & denied)}.")
        if "unauthorised" in allowed or "unauthorised" not in denied:
            errors.append(f"CCSB-T01-ACTION-UNAUTHORISED: {action_id} must explicitly deny unauthorised.")
        scope = set(action.get("scopeRequired", []))
        if not scope or scope - REQUIRED_SCOPE_DIMENSIONS:
            errors.append(f"CCSB-T01-ACTION-SCOPE: {action_id} has invalid scope {sorted(scope)}.")
        prerequisites = action.get("dataversePrerequisites", [])
        if not prerequisites:
            errors.append(f"CCSB-T01-ACTION-DATAVERSE: {action_id} must declare Dataverse prerequisites.")
        for prerequisite in prerequisites:
            privileges = prerequisite.get("privileges", [])
            if not prerequisite.get("table") or not privileges:
                errors.append(f"CCSB-T01-ACTION-DATAVERSE-REQUIREMENT: {action_id} has incomplete prerequisite.")
            invalid = [privilege for privilege in privileges if privilege not in {"Create", "Read", "Write", "Delete", "Append", "AppendTo"}]
            if invalid:
                errors.append(f"CCSB-T01-ACTION-DATAVERSE-PRIVILEGE: {action_id} invalid privileges {invalid}.")
        if action.get("directClientMutationAllowed") is not False:
            errors.append(f"CCSB-T01-ACTION-DIRECT-MUTATION: {action_id} must set directClientMutationAllowed=false.")
        if action.get("writesThroughCustomApi") is True:
            mutating_actions += 1
        if not action.get("sensitiveHandling"):
            errors.append(f"CCSB-T01-ACTION-SENSITIVE: {action_id} must define sensitive handling.")

    if REQUIRED_FLAGS - flags_covered:
        errors.append(f"CCSB-T01-FLAG-COVERAGE: Missing action coverage for flags {sorted(REQUIRED_FLAGS - flags_covered)}.")
    if mutating_actions < 6:
        errors.append("CCSB-T01-MUTATION-COVERAGE: Expected at least six Custom API-governed mutating actions.")

    negatives = matrix.get("negativeCases", [])
    negative_categories = {case.get("category") for case in negatives}
    if REQUIRED_NEGATIVE_CATEGORIES - negative_categories:
        errors.append(f"CCSB-T01-NEGATIVE-CATEGORIES: Missing categories {sorted(REQUIRED_NEGATIVE_CATEGORIES - negative_categories)}.")
    diagnostic_codes = {item.get("code") for item in matrix.get("diagnosticCatalog", [])}
    if REQUIRED_DIAGNOSTICS - diagnostic_codes:
        errors.append(f"CCSB-T01-DIAGNOSTICS: Missing diagnostics {sorted(REQUIRED_DIAGNOSTICS - diagnostic_codes)}.")
    for diagnostic in matrix.get("diagnosticCatalog", []):
        code = diagnostic.get("code", "<unknown>")
        if diagnostic.get("severity") not in {"blocking", "error", "warning"}:
            errors.append(f"CCSB-T01-DIAGNOSTIC-SEVERITY: {code} has invalid severity.")
        if not diagnostic.get("message"):
            errors.append(f"CCSB-T01-DIAGNOSTIC-MESSAGE: {code} is missing message.")
    for case in negatives:
        case_id = case.get("id", "<unknown>")
        if case.get("persona") not in REQUIRED_PERSONAS:
            errors.append(f"CCSB-T01-NEGATIVE-PERSONA: {case_id} has unknown persona.")
        if case.get("action") not in action_ids:
            errors.append(f"CCSB-T01-NEGATIVE-ACTION: {case_id} references unknown action.")
        decision = case.get("expectedDecision", {})
        if decision.get("diagnostic") not in diagnostic_codes:
            errors.append(f"CCSB-T01-NEGATIVE-DIAGNOSTIC: {case_id} references unknown diagnostic.")
        if decision.get("discloseRecordContent") is not False:
            errors.append(f"CCSB-T01-NEGATIVE-DISCLOSURE: {case_id} must prohibit record-content disclosure.")
        if case.get("category") != "support-raw-payload-request" and decision.get("allowed") is not False:
            errors.append(f"CCSB-T01-NEGATIVE-DENY: {case_id} must deny the action.")

    gates = set(matrix.get("acceptanceGates", []))
    if REQUIRED_GATES - gates:
        errors.append(f"CCSB-T01-GATES: Missing gates {sorted(REQUIRED_GATES - gates)}.")

    counts = {
        "personas": len(personas),
        "actions": len(actions),
        "scopeDimensions": len(matrix.get("scopeDimensions", [])),
        "negativeCases": len(negatives),
        "diagnostics": len(matrix.get("diagnosticCatalog", [])),
        "mutatingActions": mutating_actions,
    }
    return errors, warnings, counts


def write_report(path: Path, matrix_path: Path, errors: list[str], warnings: list[str], counts: dict[str, int]) -> None:
    generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    status = "PASS" if not errors else "FAIL"
    lines = [
        "# US-070-T01 Static Permission Matrix Validation Report",
        "",
        f"**Status:** {status}",
        f"**Generated:** {generated}",
        f"**Matrix:** `{matrix_path.relative_to(ROOT).as_posix()}`",
        "",
        "## Counts",
        "",
        f"- Personas: {counts['personas']}",
        f"- Actions: {counts['actions']}",
        f"- Scope dimensions: {counts['scopeDimensions']}",
        f"- Mutating Custom API-governed actions: {counts['mutatingActions']}",
        f"- Negative cases: {counts['negativeCases']}",
        f"- Diagnostic codes: {counts['diagnostics']}",
        f"- Errors: {len(errors)}",
        f"- Warnings: {len(warnings)}",
        "",
        "## Validation Scope",
        "",
        "- Required admin, scheduler, publisher, support, and unauthorised personas",
        "- Coverage for every `ccsb_permissionprofile` action flag from US-070-T02",
        "- Dataverse-first authorization order and CCSB restrictive permission rule",
        "- Scope dimensions for board, board version, group, location, resource, time, and field policy",
        "- Negative cases for Dataverse denial, field security, missing profile, inactive assignment, forged scope, publish, rollback, support redaction, and direct mutation",
        "- Stable diagnostic catalog and least-disclosure denial policy",
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
        "This report proves the US-070-T01 design and static matrix contract. Runtime authorization enforcement remains US-070-T03, permission-aware UI behavior remains US-070-T04, connected positive/negative role tests remain US-070-T05, and managed-solution role packaging remains US-070-T06.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate US-070-T01 permission artifacts.")
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    matrix_path = args.matrix.resolve()
    errors, warnings, counts = validate(matrix_path)
    write_report(args.report.resolve(), matrix_path, errors, warnings, counts)
    if errors:
        print(f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s).")
        for issue in errors:
            print(issue)
        return 1
    print(f"OK: {counts['personas']} personas, {counts['actions']} actions, {counts['negativeCases']} negative case(s), {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
