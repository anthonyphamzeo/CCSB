#!/usr/bin/env python3
"""Static validator for the US-002-T01 product/schema compatibility contract."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONTRACT = ROOT / "docs" / "design" / "api-contracts" / "compatibility" / "US-002-T01-compatibility-contract.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-002-T01" / "static-report.md"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
SOLUTION_VERSION = re.compile(r"^\d+\.\d+\.\d+\.\d+$")

REQUIRED_DIMENSIONS = {
    "productSemanticVersion",
    "foundationSolutionVersion",
    "configurationSchemaVersion",
    "runtimeProjectionSchemaVersion",
    "minimumSupportedProductVersion",
    "minimumSupportedConfigurationSchemaVersion",
    "minimumSupportedRuntimeProjectionSchemaVersion",
}

REQUIRED_CONSUMERS = {
    "ccsb_ValidateBoardVersion",
    "ccsb_ActivateBoardVersion",
    "configuration-service-runtime-bootstrap",
}

REQUIRED_DIAGNOSTICS = {
    "CCSB-COMPAT-PRODUCT-UNSUPPORTED",
    "CCSB-COMPAT-SCHEMA-UNSUPPORTED",
    "CCSB-COMPAT-PROJECTION-STALE",
    "CCSB-COMPAT-MIGRATION-REQUIRED",
    "CCSB-COMPAT-DOWNGRADE-BLOCKED",
    "CCSB-COMPAT-LIVE-SCHEMA-BLOCKED",
    "CCSB-COMPAT-FEATURE-FLAG-DISABLED",
}

REQUIRED_GATES = {
    "contract-versioned",
    "source-schema-version-matches",
    "supported-upgrade-paths-declared",
    "activation-consumers-declared",
    "fail-closed-rules-declared",
    "diagnostic-codes-declared",
    "existing-schema-bindings-validated",
}

REQUIRED_MIGRATION_STATES = {
    "none",
    "pending",
    "running",
    "completed",
    "failed",
    "blocked",
}


@dataclass
class Issue:
    severity: str
    code: str
    message: str


class Validator:
    def __init__(self, contract_path: Path) -> None:
        self.contract_path = contract_path
        self.contract = self.read_json(contract_path)
        self.issues: list[Issue] = []
        self.warnings: list[Issue] = []
        self.source_package = self.contract.get("sourcePackage", {})
        self.schema: dict[str, Any] = {}
        self.schema_fields: dict[str, set[str]] = {}

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def error(self, code: str, message: str) -> None:
        self.issues.append(Issue("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.warnings.append(Issue("warning", code, message))

    def validate(self) -> None:
        self.validate_header()
        self.validate_contract_document()
        self.validate_source_package()
        self.validate_versions()
        self.validate_rules_and_paths()
        self.validate_activation_policy()
        self.validate_diagnostics()
        self.validate_schema_bindings()
        self.validate_acceptance_gates()

    def validate_header(self) -> None:
        if self.contract.get("task") != "US-002-T01":
            self.error("CCSB-T01-TASK-ID", "Contract task must be US-002-T01.")
        version = self.contract.get("manifestVersion")
        if not isinstance(version, str) or not SEMVER.match(version):
            self.error("CCSB-T01-MANIFEST-VERSION", "manifestVersion must be semantic version x.y.z.")
        if not self.contract.get("name"):
            self.error("CCSB-T01-NAME", "Contract name is required.")

    def validate_contract_document(self) -> None:
        path_value = self.contract.get("contractDocument")
        if not isinstance(path_value, str):
            self.error("CCSB-T01-DOCUMENT", "contractDocument must be a workspace-relative path.")
            return
        path = ROOT / path_value
        if not path.exists():
            self.error("CCSB-T01-DOCUMENT-MISSING", f"contractDocument does not exist: {path_value}.")
            return
        text = path.read_text(encoding="utf-8-sig")
        for phrase in ("Product semantic version", "Configuration schema version", "Runtime projection", "Activation", "Supported"):
            if phrase not in text:
                self.error("CCSB-T01-DOCUMENT-COVERAGE", f"Contract document missing topic '{phrase}'.")

    def validate_source_package(self) -> None:
        required_paths = ("foundationSource", "schema", "program", "project")
        paths: dict[str, Path] = {}
        for key in required_paths:
            value = self.source_package.get(key)
            if not isinstance(value, str):
                self.error("CCSB-T01-SOURCE-PATH", f"sourcePackage.{key} must be a path.")
                continue
            path = ROOT / value
            paths[key] = path
            if not path.exists():
                self.error("CCSB-T01-SOURCE-MISSING", f"sourcePackage.{key} does not exist: {value}.")

        schema_path = paths.get("schema")
        if not schema_path or not schema_path.exists():
            return
        self.schema = self.read_json(schema_path)
        self.schema_fields = self.build_schema_fields(self.schema)

        solution = self.schema.get("solution", {})
        if self.schema.get("schemaVersion") != self.source_package.get("schemaVersion"):
            self.error("CCSB-T01-SCHEMA-VERSION", "Contract schemaVersion must match schema JSON.")
        if solution.get("uniqueName") != self.source_package.get("dataverseSolutionUniqueName"):
            self.error("CCSB-T01-SOLUTION-NAME", "Contract solution unique name must match schema JSON.")
        if solution.get("version") != self.source_package.get("targetSolutionVersion"):
            self.error("CCSB-T01-SOLUTION-VERSION", "Contract target solution version must match schema JSON.")

        project = paths.get("project")
        project_text = project.read_text(encoding="utf-8-sig") if project and project.exists() else ""
        expected_build = self.source_package.get("sourceBuildVersion")
        if expected_build and f"<Version>{expected_build}</Version>" not in project_text:
            self.error("CCSB-T01-SOURCE-BUILD", "Project version must match sourceBuildVersion.")

        program = paths.get("program")
        program_text = program.read_text(encoding="utf-8-sig") if program and program.exists() else ""
        for marker in ("ValidateLiveMetadataCompatibility", "--compatibility-report"):
            if marker not in program_text:
                self.error("CCSB-T01-PROGRAM-MARKER", f"Program.cs missing marker: {marker}.")

    @staticmethod
    def build_schema_fields(schema: dict[str, Any]) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for table in schema.get("tables", []):
            fields = {field["logicalName"] for field in table.get("fields", []) if "logicalName" in field}
            primary = table.get("primaryName", {}).get("logicalName")
            if primary:
                fields.add(primary)
            result[table.get("logicalName", "")] = fields
        for extension in schema.get("extensions", []):
            entity = extension.get("entityLogicalName")
            if not entity:
                continue
            fields = result.setdefault(entity, set())
            for field in extension.get("fields", []):
                if "logicalName" in field:
                    fields.add(field["logicalName"])
        return result

    def validate_versions(self) -> None:
        dims = self.contract.get("versionDimensions", {})
        missing = REQUIRED_DIMENSIONS - set(dims)
        if missing:
            self.error("CCSB-T01-DIMENSIONS", f"Missing version dimensions: {sorted(missing)}.")
        for key, value in dims.items():
            if key == "foundationSolutionVersion":
                if not isinstance(value, str) or not SOLUTION_VERSION.match(value):
                    self.error("CCSB-T01-SOLUTION-SEMVER", f"{key} must be x.y.z.w.")
            elif not isinstance(value, str) or not SEMVER.match(value):
                self.error("CCSB-T01-SEMVER", f"{key} must be x.y.z.")

        if dims.get("configurationSchemaVersion") != self.source_package.get("schemaVersion"):
            self.error("CCSB-T01-DIM-SCHEMA-MATCH", "configurationSchemaVersion must match source schemaVersion.")
        if dims.get("foundationSolutionVersion") != self.source_package.get("targetSolutionVersion"):
            self.error("CCSB-T01-DIM-SOLUTION-MATCH", "foundationSolutionVersion must match targetSolutionVersion.")

    def validate_rules_and_paths(self) -> None:
        rules = self.contract.get("compatibilityRules", {})
        for flag in (
            "productMajorMustMatch",
            "configurationSchemaMajorMustMatch",
            "runtimeProjectionMajorMustMatch",
            "unsupportedDowngradeBlocksActivation",
            "missingVersionBlocksActivation",
            "staleProjectionBlocksRuntime",
            "pendingMigrationBlocksActivation",
            "liveSchemaCompatibilityReportRequired",
        ):
            if rules.get(flag) is not True:
                self.error("CCSB-T01-RULE-FLAG", f"compatibilityRules.{flag} must be true.")

        dims = self.contract.get("versionDimensions", {})
        if dims.get("configurationSchemaVersion") not in rules.get("supportedConfigurationSchemaVersions", []):
            self.error("CCSB-T01-SUPPORTED-SCHEMA", "Current configuration schema version must be supported.")
        if dims.get("runtimeProjectionSchemaVersion") not in rules.get("supportedRuntimeProjectionSchemaVersions", []):
            self.error("CCSB-T01-SUPPORTED-PROJECTION", "Current runtime projection schema version must be supported.")

        paths = self.contract.get("supportedUpgradePaths", [])
        if not isinstance(paths, list) or len(paths) < 2:
            self.error("CCSB-T01-UPGRADE-PATHS", "At least initial install and same-line patch paths are required.")
            return
        seen_ids: set[str] = set()
        for path in paths:
            path_id = path.get("id", "<unknown>")
            if path_id in seen_ids:
                self.error("CCSB-T01-UPGRADE-ID", f"Duplicate upgrade path id: {path_id}.")
            seen_ids.add(path_id)
            if path.get("activationAllowed") is not True:
                self.error("CCSB-T01-UPGRADE-ACTIVATION", f"{path_id} must declare activationAllowed=true.")
            if not isinstance(path.get("requiredEvidence"), list) or not path["requiredEvidence"]:
                self.error("CCSB-T01-UPGRADE-EVIDENCE", f"{path_id} must declare requiredEvidence.")
            to_dims = path.get("to", {})
            for dim in ("productSemanticVersion", "configurationSchemaVersion", "runtimeProjectionSchemaVersion"):
                if to_dims.get(dim) != dims.get(dim):
                    self.error("CCSB-T01-UPGRADE-TARGET", f"{path_id} target {dim} must match current contract.")

        blocked = self.contract.get("blockedTransitions", [])
        blocked_codes = {item.get("diagnosticCode") for item in blocked if isinstance(item, dict)}
        for code in REQUIRED_DIAGNOSTICS - {"CCSB-COMPAT-FEATURE-FLAG-DISABLED"}:
            if code not in blocked_codes:
                self.error("CCSB-T01-BLOCKED-COVERAGE", f"Blocked transitions must reference {code}.")

        states = {item.get("value"): item for item in self.contract.get("migrationStates", []) if isinstance(item, dict)}
        missing_states = REQUIRED_MIGRATION_STATES - set(states)
        if missing_states:
            self.error("CCSB-T01-MIGRATION-STATES", f"Missing migration states: {sorted(missing_states)}.")
        for value in ("pending", "running", "failed", "blocked"):
            if states.get(value, {}).get("activationAllowed") is not False:
                self.error("CCSB-T01-MIGRATION-BLOCK", f"Migration state {value} must block activation.")
        for value in ("none", "completed"):
            if states.get(value, {}).get("activationAllowed") is not True:
                self.error("CCSB-T01-MIGRATION-ALLOW", f"Migration state {value} must allow activation.")

    def validate_activation_policy(self) -> None:
        policy = self.contract.get("activationPolicy", {})
        if policy.get("failClosed") is not True:
            self.error("CCSB-T01-FAIL-CLOSED", "activationPolicy.failClosed must be true.")
        consumers = set(policy.get("consumers", []))
        missing = REQUIRED_CONSUMERS - consumers
        if missing:
            self.error("CCSB-T01-CONSUMERS", f"Missing activation consumers: {sorted(missing)}.")
        for flag in (
            "requiresCurrentProjection",
            "requiresZeroPendingMigrations",
            "requiresCompatibilityReportZeroBlockers",
            "writesValidationResults",
        ):
            if policy.get(flag) is not True:
                self.error("CCSB-T01-ACTIVATION-FLAG", f"activationPolicy.{flag} must be true.")
        if not {"blocking", "error"}.issubset(set(policy.get("blockOnSeverities", []))):
            self.error("CCSB-T01-BLOCK-SEVERITIES", "Activation must block on blocking and error severities.")

    def validate_diagnostics(self) -> None:
        diagnostics = self.contract.get("diagnosticCodes", [])
        by_code = {item.get("code"): item for item in diagnostics if isinstance(item, dict)}
        missing = REQUIRED_DIAGNOSTICS - set(by_code)
        if missing:
            self.error("CCSB-T01-DIAGNOSTICS", f"Missing diagnostic codes: {sorted(missing)}.")
        for code, item in by_code.items():
            if not isinstance(code, str) or not code.startswith("CCSB-COMPAT-"):
                self.error("CCSB-T01-DIAGNOSTIC-PREFIX", f"Invalid diagnostic code: {code}.")
            if item.get("severity") not in {"blocking", "error", "warning", "info"}:
                self.error("CCSB-T01-DIAGNOSTIC-SEVERITY", f"{code} has invalid severity.")
            if not item.get("category") or not item.get("message") or not item.get("recommendedAction"):
                self.error("CCSB-T01-DIAGNOSTIC-CONTENT", f"{code} must include category, message, and recommendedAction.")

    def validate_schema_bindings(self) -> None:
        if not self.schema_fields:
            self.warn("CCSB-T01-SCHEMA-BINDINGS-SKIPPED", "Schema field bindings skipped because schema did not load.")
            return
        for binding in self.contract.get("existingSchemaBindings", []):
            entity = binding.get("entity")
            if entity not in self.schema_fields:
                self.error("CCSB-T01-BINDING-ENTITY", f"Unknown binding entity: {entity}.")
                continue
            for field in binding.get("fields", []):
                if field not in self.schema_fields[entity]:
                    self.error("CCSB-T01-BINDING-FIELD", f"Unknown binding field: {entity}.{field}.")

    def validate_acceptance_gates(self) -> None:
        gates = set(self.contract.get("acceptanceGates", []))
        missing = REQUIRED_GATES - gates
        if missing:
            self.error("CCSB-T01-GATES", f"Missing acceptance gates: {sorted(missing)}.")

    def write_report(self, report_path: Path) -> None:
        status = "PASS" if not self.issues else "FAIL"
        generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        paths = self.contract.get("supportedUpgradePaths", [])
        diagnostics = self.contract.get("diagnosticCodes", [])
        bindings = self.contract.get("existingSchemaBindings", [])
        gates = self.contract.get("acceptanceGates", [])

        lines = [
            "# US-002-T01 Static Compatibility Contract Report",
            "",
            f"**Status:** {status}",
            f"**Generated:** {generated}",
            f"**Contract:** `{self.contract_path.relative_to(ROOT).as_posix()}`",
            "",
            "## Counts",
            "",
            f"- Supported upgrade paths: {len(paths)}",
            f"- Diagnostic codes: {len(diagnostics)}",
            f"- Existing schema binding groups: {len(bindings)}",
            f"- Acceptance gates: {len(gates)}",
            f"- Errors: {len(self.issues)}",
            f"- Warnings: {len(self.warnings)}",
            "",
            "## Validation Scope",
            "",
            "- Contract header, document coverage, and source package paths",
            "- Product, solution, configuration schema, and runtime projection versions",
            "- Supported upgrade paths, blocked transitions, and migration states",
            "- Fail-closed activation policy and Custom API consumers",
            "- Stable diagnostic code coverage",
            "- Existing Dataverse schema field bindings",
            "",
            "## Supported Paths",
            "",
        ]
        for path in paths:
            lines.append(f"- `{path.get('id', '<unknown>')}` {path.get('name', '')}")
        lines.extend(["", "## Issues", ""])
        if not self.issues and not self.warnings:
            lines.append("- None")
        for issue in self.issues + self.warnings:
            lines.append(f"- [{issue.severity.upper()}] `{issue.code}` - {issue.message}")
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This is a static contract validation. Runtime Custom API implementation, explicit metadata columns, live Dataverse upgrade execution, and administrator diagnostics remain downstream US-002 tasks.",
                "",
            ]
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the US-002-T01 compatibility contract.")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    validator = Validator(args.contract.resolve())
    validator.validate()
    validator.write_report(args.report.resolve())

    if validator.issues:
        print(f"FAIL: {len(validator.issues)} error(s), {len(validator.warnings)} warning(s).")
        for issue in validator.issues:
            print(f"{issue.code}: {issue.message}")
        return 1

    print(
        f"OK: {len(validator.contract.get('supportedUpgradePaths', []))} supported paths, "
        f"{len(validator.contract.get('diagnosticCodes', []))} diagnostic codes, "
        f"{len(validator.warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

