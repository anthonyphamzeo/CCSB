#!/usr/bin/env python3
"""Static validator for the US-004-T10 schema migration and upgrade policy."""
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
DEFAULT_MANIFEST = ROOT / "tests" / "Fixtures" / "Upgrade" / "US-004-T10-upgrade-rehearsal-manifest.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-004-T10" / "static-report.md"

REQUIRED_ALLOWED_CHANGE_TYPES = {
    "add-table",
    "add-optional-field",
    "add-choice-option",
    "add-restrict-lookup-relationship",
    "add-alternate-key-before-use",
    "add-nonblocking-validation-rule",
    "add-idempotent-backfill",
    "add-side-by-side-projection-version",
}

REQUIRED_PROHIBITED_CHANGE_TYPES = {
    "delete-table",
    "delete-field",
    "rename-logical-name",
    "repurpose-choice-value",
    "change-field-type",
    "reduce-string-length",
    "tighten-required-level-before-backfill",
    "change-delete-behavior-from-restrict",
    "mutate-active-boardversion",
    "mutate-publishsnapshot",
    "delete-audit-or-outbox-records",
    "import-unmanaged-to-production",
}

REQUIRED_FEATURE_FLAGS = {
    "ccsb.foundation.schema.1.0.0.1",
    "ccsb.runtime.projection.1.0.0",
    "ccsb.nativeGraph.enabled",
}

REQUIRED_STAGE_CATEGORIES = {
    "static-validation",
    "live-validation",
    "managed-export",
    "managed-import",
    "precheck-snapshot",
    "backfill",
    "compatibility-validation",
    "feature-activation",
    "rollback-drill",
    "postcheck-snapshot",
}

REQUIRED_DATA_PROTECTION_ASSERTIONS = {
    "active-board-version-unchanged-until-lifecycle-activation",
    "publish-snapshot-and-items-hash-stable",
    "operation-audit-and-outbox-append-only",
    "publish-locks-retained-with-expiry-and-retention",
    "runtime-projections-versioned-side-by-side",
    "schedule-change-rollback-images-preserved",
}

REQUIRED_ACCEPTANCE_GATES = {
    "static-policy-validator-pass",
    "foundation-schema-validator-pass",
    "dotnet-build-pass",
    "live-compatibility-report-zero-blockers",
    "managed-import-rehearsal-pass",
    "backfill-idempotency-pass",
    "protected-record-counts-and-hashes-stable",
    "rollback-drill-pass",
}

PROTECTED_ENTITIES = {
    "ccsb_boardversion",
    "ccsb_runtimeprojection",
    "ccsb_publishsnapshot",
    "ccsb_publishsnapshotitem",
    "ccsb_schedulechange",
    "ccsb_operationaudit",
    "ccsb_outboxevent",
}


@dataclass
class Issue:
    severity: str
    code: str
    message: str


class Validator:
    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path
        self.manifest = self.read_json(manifest_path)
        self.issues: list[Issue] = []
        self.warnings: list[Issue] = []
        self.source_package = self.manifest.get("sourcePackage", {})
        self.change_policy = self.manifest.get("changePolicy", {})
        self.rehearsal = self.manifest.get("rehearsal", {})

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def error(self, code: str, message: str) -> None:
        self.issues.append(Issue("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.warnings.append(Issue("warning", code, message))

    def validate(self) -> None:
        self.validate_header()
        self.validate_documents()
        self.validate_source_package()
        self.validate_change_policy()
        self.validate_rehearsal()

    def validate_header(self) -> None:
        if self.manifest.get("task") != "US-004-T10":
            self.error("CCSB-T10-TASK-ID", "Manifest task must be US-004-T10.")
        version = self.manifest.get("manifestVersion")
        if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+$", version):
            self.error("CCSB-T10-MANIFEST-VERSION", "manifestVersion must be semantic version x.y.z.")
        if not self.manifest.get("name"):
            self.error("CCSB-T10-MANIFEST-NAME", "Manifest name is required.")

    def validate_documents(self) -> None:
        for key in ("policyDocument", "sourcePolicyDocument"):
            value = self.manifest.get(key)
            if not isinstance(value, str):
                self.error("CCSB-T10-DOCUMENT-PATH", f"{key} must be a workspace-relative path.")
                continue
            path = ROOT / value
            if not path.exists():
                self.error("CCSB-T10-DOCUMENT-MISSING", f"{key} does not exist: {value}.")
                continue
            text = path.read_text(encoding="utf-8-sig")
            for phrase in (
                "Additive",
                "Destructive",
                "Backfill",
                "Feature",
                "Compatibility",
                "Rollback",
                "managed",
            ):
                if phrase not in text:
                    self.error("CCSB-T10-DOCUMENT-COVERAGE", f"{value} missing required topic '{phrase}'.")

    def validate_source_package(self) -> None:
        required_path_keys = [
            "foundationSource",
            "schema",
            "program",
            "runWrapper",
            "interactiveWrapper",
            "project",
        ]
        paths: dict[str, Path] = {}
        for key in required_path_keys:
            value = self.source_package.get(key)
            if not isinstance(value, str):
                self.error("CCSB-T10-SOURCE-PATH", f"sourcePackage.{key} must be a path.")
                continue
            path = ROOT / value
            paths[key] = path
            if not path.exists():
                self.error("CCSB-T10-SOURCE-MISSING", f"sourcePackage.{key} does not exist: {value}.")

        if not paths.get("schema") or not paths["schema"].exists():
            return

        schema = self.read_json(paths["schema"])
        solution = schema.get("solution", {})
        if schema.get("schemaVersion") != self.source_package.get("schemaVersion"):
            self.error("CCSB-T10-SCHEMA-VERSION", "Manifest schemaVersion must match schema JSON.")
        if solution.get("uniqueName") != self.source_package.get("dataverseSolutionUniqueName"):
            self.error("CCSB-T10-SOLUTION-NAME", "Manifest solution unique name must match schema JSON.")
        if solution.get("version") != self.source_package.get("targetSolutionVersion"):
            self.error("CCSB-T10-SOLUTION-VERSION", "Manifest solution version must match schema JSON.")
        if schema.get("relationshipPolicy", {}).get("delete") != "Restrict":
            self.error("CCSB-T10-DELETE-POLICY", "Foundation schema relationship policy must be Delete Restrict.")
        if len(schema.get("tables", [])) != 14:
            self.error("CCSB-T10-TABLE-COUNT", "Foundation schema must still define 14 foundation tables.")

        project_path = paths.get("project")
        project_text = project_path.read_text(encoding="utf-8-sig") if project_path and project_path.exists() else ""
        expected_build = self.source_package.get("sourceBuildVersion")
        if expected_build and f"<Version>{expected_build}</Version>" not in project_text:
            self.error("CCSB-T10-SOURCE-BUILD-VERSION", "Project version must match sourceBuildVersion.")

        program_path = paths.get("program")
        program_text = program_path.read_text(encoding="utf-8-sig") if program_path and program_path.exists() else ""
        for marker in (
            "--export-managed",
            "ExportManaged",
            "Managed = _options.ExportManaged",
            "CCSB_FoundationSchema_1_0_0_1_managed.zip",
            "ValidateLiveMetadataCompatibility",
            "--compatibility-report",
        ):
            if marker not in program_text:
                self.error("CCSB-T10-PROGRAM-MARKER", f"Program.cs missing marker: {marker}.")

        for key in ("runWrapper", "interactiveWrapper"):
            wrapper_path = paths.get(key)
            wrapper_text = wrapper_path.read_text(encoding="utf-8-sig") if wrapper_path and wrapper_path.exists() else ""
            for marker in ("ExportManaged", "CCSB_FoundationSchema_1_0_0_1_managed.zip"):
                if marker not in wrapper_text:
                    self.error("CCSB-T10-WRAPPER-MARKER", f"{key} missing marker: {marker}.")

        switches = set(self.source_package.get("managedExportSwitches", []))
        for switch in ("-ExportManaged", "--export-managed"):
            if switch not in switches:
                self.error("CCSB-T10-MANAGED-SWITCH", f"managedExportSwitches missing {switch}.")
        if not str(self.source_package.get("managedPackage", "")).endswith("_managed.zip"):
            self.error("CCSB-T10-MANAGED-PACKAGE", "managedPackage must name a managed ZIP.")

    def validate_change_policy(self) -> None:
        allowed = set(self.change_policy.get("allowedChangeTypes", []))
        missing_allowed = REQUIRED_ALLOWED_CHANGE_TYPES - allowed
        if missing_allowed:
            self.error("CCSB-T10-ALLOWED-CHANGES", f"Missing allowed change types: {sorted(missing_allowed)}.")

        prohibited = set(self.change_policy.get("prohibitedChangeTypes", []))
        missing_prohibited = REQUIRED_PROHIBITED_CHANGE_TYPES - prohibited
        if missing_prohibited:
            self.error("CCSB-T10-PROHIBITED-CHANGES", f"Missing prohibited change types: {sorted(missing_prohibited)}.")

        self.validate_backfills()
        self.validate_feature_flags()
        self.validate_compatibility_periods()
        self.validate_rollback_limits()

    def validate_backfills(self) -> None:
        backfills = self.change_policy.get("backfillRules", [])
        if not isinstance(backfills, list) or len(backfills) < 3:
            self.error("CCSB-T10-BACKFILL-COUNT", "At least three backfill rules are required.")
            return

        covered_entities: set[str] = set()
        for rule in backfills:
            rule_id = rule.get("id", "<unknown>")
            if rule.get("mode") != "additive":
                self.error("CCSB-T10-BACKFILL-MODE", f"{rule_id} must use additive mode.")
            for boolean_field in ("runAfterManagedImport", "idempotent", "auditRequired"):
                if rule.get(boolean_field) is not True:
                    self.error("CCSB-T10-BACKFILL-BOOLEAN", f"{rule_id} must set {boolean_field}=true.")
            if rule.get("mutatesImmutableArtifacts") is not False:
                self.error("CCSB-T10-BACKFILL-IMMUTABLE", f"{rule_id} must not mutate immutable artifacts.")
            target_entities = rule.get("targetEntities", [])
            if not isinstance(target_entities, list) or not target_entities:
                self.error("CCSB-T10-BACKFILL-TARGETS", f"{rule_id} must target at least one entity.")
            else:
                covered_entities.update(str(entity) for entity in target_entities)
            if not rule.get("scopeKey"):
                self.error("CCSB-T10-BACKFILL-SCOPE", f"{rule_id} must define a scopeKey.")

        missing_protected = PROTECTED_ENTITIES - covered_entities
        if missing_protected:
            self.error("CCSB-T10-BACKFILL-PROTECTED-COVERAGE", f"Backfill rules must cover protected entities: {sorted(missing_protected)}.")

    def validate_feature_flags(self) -> None:
        flags = self.change_policy.get("featureFlags", [])
        if not isinstance(flags, list):
            self.error("CCSB-T10-FEATURE-FLAGS", "featureFlags must be an array.")
            return
        by_key = {flag.get("key"): flag for flag in flags if isinstance(flag, dict)}
        missing = REQUIRED_FEATURE_FLAGS - set(by_key)
        if missing:
            self.error("CCSB-T10-FEATURE-FLAG-COVERAGE", f"Missing feature flags: {sorted(missing)}.")
        for key, flag in by_key.items():
            if flag.get("defaultState") != "off":
                self.error("CCSB-T10-FEATURE-FLAG-DEFAULT", f"Feature flag {key} must default off.")
            if not flag.get("enableAfter"):
                self.error("CCSB-T10-FEATURE-FLAG-GATE", f"Feature flag {key} must define enableAfter.")

    def validate_compatibility_periods(self) -> None:
        periods = self.change_policy.get("compatibilityPeriods", [])
        if not isinstance(periods, list) or not periods:
            self.error("CCSB-T10-COMPATIBILITY-PERIOD", "At least one compatibility period is required.")
            return
        for period in periods:
            if period.get("minimumDays", 0) < 90:
                self.error("CCSB-T10-COMPATIBILITY-DAYS", "Compatibility period must be at least 90 days.")
            for field in ("priorBoardVersionsReadable", "priorProjectionVersionsReadable"):
                if period.get(field) is not True:
                    self.error("CCSB-T10-COMPATIBILITY-READABLE", f"Compatibility period must set {field}=true.")

    def validate_rollback_limits(self) -> None:
        rollback = self.change_policy.get("rollbackLimits", {})
        if rollback.get("schemaRollbackSupported") is not False:
            self.error("CCSB-T10-ROLLBACK-SCHEMA", "schemaRollbackSupported must be false.")
        if rollback.get("metadataRepairStrategy") != "additive-forward-managed-solution":
            self.error("CCSB-T10-ROLLBACK-REPAIR", "metadataRepairStrategy must be additive-forward-managed-solution.")
        for field in ("runtimeRollbackMechanism", "dataRollbackMechanism"):
            value = rollback.get(field)
            if not isinstance(value, str) or len(value) < 20:
                self.error("CCSB-T10-ROLLBACK-MECHANISM", f"rollbackLimits.{field} must be descriptive.")
        immutable = set(rollback.get("immutableArtifacts", []))
        for required in ("ccsb_publishsnapshot", "ccsb_operationaudit", "ccsb_outboxevent"):
            if not any(required in value for value in immutable):
                self.error("CCSB-T10-ROLLBACK-IMMUTABLE", f"immutableArtifacts must include {required}.")

    def validate_rehearsal(self) -> None:
        stages = self.rehearsal.get("stages", [])
        if not isinstance(stages, list):
            self.error("CCSB-T10-REHEARSAL-STAGES", "rehearsal.stages must be an array.")
            return
        categories = {stage.get("category") for stage in stages if isinstance(stage, dict)}
        missing_categories = REQUIRED_STAGE_CATEGORIES - categories
        if missing_categories:
            self.error("CCSB-T10-REHEARSAL-COVERAGE", f"Missing rehearsal categories: {sorted(missing_categories)}.")

        assertions = set(self.rehearsal.get("dataProtectionAssertions", []))
        missing_assertions = REQUIRED_DATA_PROTECTION_ASSERTIONS - assertions
        if missing_assertions:
            self.error("CCSB-T10-DATA-PROTECTION", f"Missing data protection assertions: {sorted(missing_assertions)}.")

        gates = set(self.rehearsal.get("acceptanceGates", []))
        missing_gates = REQUIRED_ACCEPTANCE_GATES - gates
        if missing_gates:
            self.error("CCSB-T10-ACCEPTANCE-GATES", f"Missing acceptance gates: {sorted(missing_gates)}.")

        environments = self.rehearsal.get("environments", [])
        if not any("DEV" in env and "managed export" in env for env in environments):
            self.error("CCSB-T10-ENVIRONMENTS", "Rehearsal must include DEV managed export environment.")
        if not any("TEST" in env and "managed import" in env for env in environments):
            self.error("CCSB-T10-ENVIRONMENTS", "Rehearsal must include TEST managed import environment.")

    def write_report(self, report_path: Path) -> None:
        status = "PASS" if not self.issues else "FAIL"
        generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        stages = self.rehearsal.get("stages", []) if isinstance(self.rehearsal.get("stages", []), list) else []
        backfills = self.change_policy.get("backfillRules", []) if isinstance(self.change_policy.get("backfillRules", []), list) else []
        flags = self.change_policy.get("featureFlags", []) if isinstance(self.change_policy.get("featureFlags", []), list) else []

        lines = [
            "# US-004-T10 Static Upgrade Policy Report",
            "",
            f"**Status:** {status}",
            f"**Generated:** {generated}",
            f"**Manifest:** `{self.manifest_path.relative_to(ROOT).as_posix()}`",
            "",
            "## Counts",
            "",
            f"- Rehearsal stages: {len(stages)}",
            f"- Backfill rules: {len(backfills)}",
            f"- Feature flags: {len(flags)}",
            f"- Errors: {len(self.issues)}",
            f"- Warnings: {len(self.warnings)}",
            "",
            "## Validation Scope",
            "",
            "- Manifest header and policy document coverage",
            "- Foundation schema version, solution version, Delete Restrict policy, and table count",
            "- Managed export support in Program.cs and PowerShell wrappers",
            "- Additive migration and destructive-change policy coverage",
            "- Backfill idempotency, audit, scope, and protected-entity coverage",
            "- Feature flags, compatibility period, and rollback limits",
            "- Managed upgrade rehearsal stages, data protection assertions, and acceptance gates",
            "",
            "## Rehearsal Stages",
            "",
        ]
        for stage in stages:
            lines.append(f"- `{stage.get('id', '<unknown>')}` {stage.get('category', '<unknown>')} - {stage.get('name', '')}")
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
                "This is a static policy and rehearsal-contract validation. Live managed import, connected Dataverse compatibility validation, and production approval remain environment release activities.",
                "",
            ]
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the US-004-T10 schema migration and upgrade policy manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    validator = Validator(args.manifest.resolve())
    validator.validate()
    validator.write_report(args.report.resolve())

    if validator.issues:
        print(f"FAIL: {len(validator.issues)} error(s), {len(validator.warnings)} warning(s).")
        for issue in validator.issues:
            print(f"{issue.code}: {issue.message}")
        return 1

    print(
        f"OK: {len(validator.rehearsal.get('stages', []))} rehearsal stages, "
        f"{len(validator.change_policy.get('backfillRules', []))} backfill rules, "
        f"{len(validator.change_policy.get('featureFlags', []))} feature flags, "
        f"{len(validator.warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())