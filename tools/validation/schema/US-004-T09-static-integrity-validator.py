#!/usr/bin/env python3
"""Static integrity validator for the US-004-T09 deterministic seed manifest."""
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
DEFAULT_MANIFEST = ROOT / "tests" / "Fixtures" / "Schema" / "US-004-T09-seed-manifest.json"
DEFAULT_REPORT = ROOT / "docs" / "implementation" / "testing" / "evidence" / "US-004-T09" / "static-report.md"


@dataclass
class Issue:
    severity: str
    code: str
    message: str


class Validator:
    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path
        self.issues: list[Issue] = []
        self.warnings: list[Issue] = []
        self.manifest = self.read_json(manifest_path)
        self.catalog = self.build_catalog()

    @staticmethod
    def read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def error(self, code: str, message: str) -> None:
        self.issues.append(Issue("error", code, message))

    def warn(self, code: str, message: str) -> None:
        self.warnings.append(Issue("warning", code, message))

    def build_catalog(self) -> dict[str, Any]:
        source_paths = self.manifest.get("sourceSchemas", {})
        foundation = self.read_json(ROOT / source_paths["foundation"])
        audit = self.read_json(ROOT / source_paths["audit"])
        core = self.read_json(ROOT / source_paths["core"])

        entities: dict[str, dict[str, Any]] = {}
        lookup_targets: dict[tuple[str, str], set[str]] = {}
        required_lookups: dict[str, set[str]] = {}

        def add_table(table: dict[str, Any], source: str, primary_field: str | None = None) -> None:
            logical_name = table["logicalName"]
            primary = primary_field or table.get("primaryName", {}).get("logicalName", "ccsb_name")
            entity = entities.setdefault(
                logical_name,
                {
                    "source": source,
                    "fields": {},
                    "primary": primary,
                    "alternateKeys": [],
                },
            )
            entity["fields"].setdefault(primary, {"logicalName": primary, "type": "String", "required": True})
            for field in table.get("fields", []):
                entity["fields"][field["logicalName"]] = field
            for key in table.get("alternateKeys", []):
                entity.setdefault("alternateKeys", []).append(key)

        for table in foundation.get("tables", []):
            add_table(table, "foundation")
        for table in audit.get("tables", []):
            add_table(table, "audit")

        core_primary = core.get("primaryName", {}).get("logicalName", "ccsb_name")
        for table in core.get("tables", []):
            add_table(table, "core", core_primary)

        for extension in foundation.get("extensions", []):
            entity = entities.setdefault(
                extension["entityLogicalName"],
                {
                    "source": "foundation-extension",
                    "fields": {"ccsb_name": {"logicalName": "ccsb_name", "type": "String", "required": True}},
                    "primary": "ccsb_name",
                    "alternateKeys": [],
                },
            )
            for field in extension.get("fields", []):
                entity["fields"][field["logicalName"]] = field

        for schema in (foundation, audit):
            for rel in schema.get("relationships", []):
                referencing = rel["referencingEntity"]
                lookup = rel["lookupLogicalName"]
                referenced = rel["referencedEntity"]
                lookup_targets.setdefault((referencing, lookup), set()).add(referenced)
                if rel.get("required") is True:
                    required_lookups.setdefault(referencing, set()).add(lookup)

        return {
            "entities": entities,
            "lookupTargets": lookup_targets,
            "requiredLookups": required_lookups,
        }

    def validate(self) -> None:
        self.validate_header()
        records = self.manifest.get("records", [])
        record_map = self.validate_records(records)
        self.validate_required_coverage(records)
        self.validate_negative_fixtures(record_map)
        self.validate_business_rules(records, record_map)

    def validate_header(self) -> None:
        version = self.manifest.get("manifestVersion")
        if not isinstance(version, str) or not re.match(r"^\d+\.\d+\.\d+$", version):
            self.error("CCSB-T09-MANIFEST-VERSION", "manifestVersion must be semantic version x.y.z.")
        if self.manifest.get("task") != "US-004-T09":
            self.error("CCSB-T09-TASK-ID", "Manifest task must be US-004-T09.")
        clock = self.manifest.get("fixedClockUtc")
        if not self.is_datetime(clock):
            self.error("CCSB-T09-FIXED-CLOCK", "fixedClockUtc must be an ISO UTC timestamp.")

    def validate_records(self, records: Any) -> dict[str, dict[str, Any]]:
        if not isinstance(records, list) or not records:
            self.error("CCSB-T09-EMPTY-RECORDS", "records must be a non-empty array.")
            return {}

        record_map: dict[str, dict[str, Any]] = {}
        seed_keys: set[tuple[str, str]] = set()
        for record in records:
            record_id = record.get("id")
            entity = record.get("entity")
            if not record_id or not isinstance(record_id, str):
                self.error("CCSB-T09-RECORD-ID", f"Record has invalid id: {record!r}")
                continue
            if record_id in record_map:
                self.error("CCSB-T09-DUPLICATE-RECORD-ID", f"Duplicate record id: {record_id}")
            record_map[record_id] = record

            if entity not in self.catalog["entities"]:
                self.error("CCSB-T09-UNKNOWN-ENTITY", f"{record_id} references unknown entity {entity}.")
                continue

            seed_key = record.get("seedKey")
            if not isinstance(seed_key, dict) or not seed_key:
                self.error("CCSB-T09-MISSING-SEED-KEY", f"{record_id} must define a deterministic seedKey.")
            else:
                serialized = json.dumps(seed_key, sort_keys=True, separators=(",", ":"))
                key = (entity, serialized)
                if key in seed_keys:
                    self.error("CCSB-T09-DUPLICATE-SEED-KEY", f"{record_id} duplicates seedKey {serialized}.")
                seed_keys.add(key)

            self.validate_attributes(record)

        for record in records:
            if record.get("entity") in self.catalog["entities"]:
                self.validate_references(record, record_map)

        return record_map

    def validate_attributes(self, record: dict[str, Any]) -> None:
        entity_name = record["entity"]
        entity = self.catalog["entities"][entity_name]
        fields = entity["fields"]
        attributes = record.get("attributes", {})
        if not isinstance(attributes, dict):
            self.error("CCSB-T09-ATTRIBUTES", f"{record['id']} attributes must be an object.")
            return

        primary = entity.get("primary", "ccsb_name")
        if primary not in attributes:
            self.error("CCSB-T09-MISSING-PRIMARY-NAME", f"{record['id']} must include {primary}.")

        for field_name, value in attributes.items():
            field = fields.get(field_name)
            if field is None:
                self.error("CCSB-T09-UNKNOWN-FIELD", f"{record['id']} has unknown field {entity_name}.{field_name}.")
                continue
            self.validate_field_value(record["id"], entity_name, field, value)

        for field_name, field in fields.items():
            if field.get("required") is True and field_name not in attributes:
                self.error("CCSB-T09-MISSING-REQUIRED-FIELD", f"{record['id']} missing {entity_name}.{field_name}.")

    def validate_field_value(self, record_id: str, entity: str, field: dict[str, Any], value: Any) -> None:
        field_name = field["logicalName"]
        field_type = field.get("type", "String")
        prefix = f"{record_id} {entity}.{field_name}"
        if field_type in {"String", "Memo"}:
            if not isinstance(value, str):
                self.error("CCSB-T09-FIELD-TYPE", f"{prefix} must be a string.")
                return
            max_length = field.get("maxLength")
            if isinstance(max_length, int) and len(value) > max_length:
                self.error("CCSB-T09-FIELD-LENGTH", f"{prefix} exceeds max length {max_length}.")
        elif field_type == "Boolean":
            if not isinstance(value, bool):
                self.error("CCSB-T09-FIELD-TYPE", f"{prefix} must be a boolean.")
        elif field_type == "Integer":
            if not isinstance(value, int) or isinstance(value, bool):
                self.error("CCSB-T09-FIELD-TYPE", f"{prefix} must be an integer.")
            self.validate_number_range(prefix, field, value)
        elif field_type == "Decimal":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                self.error("CCSB-T09-FIELD-TYPE", f"{prefix} must be numeric.")
            self.validate_number_range(prefix, field, float(value))
        elif field_type == "Choice":
            options = {option["value"] for option in field.get("choiceOptions", [])}
            if value not in options:
                self.error("CCSB-T09-CHOICE-VALUE", f"{prefix} has unsupported choice value {value}.")
        elif field_type in {"DateOnly"}:
            if not isinstance(value, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                self.error("CCSB-T09-DATE-VALUE", f"{prefix} must be yyyy-mm-dd.")
        elif field_type in {"DateAndTime", "DateTime"}:
            if not self.is_datetime(value):
                self.error("CCSB-T09-DATETIME-VALUE", f"{prefix} must be an ISO UTC timestamp.")
        else:
            self.warn("CCSB-T09-FIELD-TYPE-UNVALIDATED", f"{prefix} has unhandled type {field_type}.")

    def validate_number_range(self, prefix: str, field: dict[str, Any], value: int | float) -> None:
        min_value = field.get("minValue")
        max_value = field.get("maxValue")
        if min_value is not None and value < min_value:
            self.error("CCSB-T09-NUMBER-RANGE", f"{prefix} is below minValue {min_value}.")
        if max_value is not None and value > max_value:
            self.error("CCSB-T09-NUMBER-RANGE", f"{prefix} exceeds maxValue {max_value}.")

    @staticmethod
    def is_datetime(value: Any) -> bool:
        if not isinstance(value, str):
            return False
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value.endswith("Z") or value.endswith("+00:00")
        except ValueError:
            return False

    def validate_references(self, record: dict[str, Any], record_map: dict[str, dict[str, Any]]) -> None:
        entity = record["entity"]
        references = record.get("references", [])
        if not isinstance(references, list):
            self.error("CCSB-T09-REFERENCES", f"{record['id']} references must be an array.")
            return

        seen_fields = {ref.get("field") for ref in references if isinstance(ref, dict)}
        for required_lookup in self.catalog["requiredLookups"].get(entity, set()):
            if required_lookup not in seen_fields:
                self.error("CCSB-T09-MISSING-REQUIRED-LOOKUP", f"{record['id']} missing {required_lookup}.")

        for ref in references:
            field = ref.get("field")
            target_entity = ref.get("entity")
            target_id = ref.get("id")
            targets = self.catalog["lookupTargets"].get((entity, field))
            if not targets:
                self.error("CCSB-T09-UNKNOWN-LOOKUP", f"{record['id']} has unknown lookup {entity}.{field}.")
                continue
            if target_entity not in targets:
                allowed = ", ".join(sorted(targets))
                self.error(
                    "CCSB-T09-LOOKUP-TARGET",
                    f"{record['id']} {entity}.{field} targets {target_entity}; expected one of {allowed}.",
                )
            target = record_map.get(target_id)
            if not target:
                self.error("CCSB-T09-UNRESOLVED-REFERENCE", f"{record['id']} references missing id {target_id}.")
            elif target.get("entity") != target_entity:
                self.error(
                    "CCSB-T09-REFERENCE-ENTITY",
                    f"{record['id']} reference {target_id} is {target.get('entity')}, not {target_entity}.",
                )

    def validate_required_coverage(self, records: list[dict[str, Any]]) -> None:
        present = {record.get("entity") for record in records}
        for entity in self.manifest.get("requiredEntityCoverage", []):
            if entity not in present:
                self.error("CCSB-T09-COVERAGE", f"Required seed coverage missing entity {entity}.")

    def validate_negative_fixtures(self, record_map: dict[str, dict[str, Any]]) -> None:
        fixtures = self.manifest.get("negativeFixtures", [])
        if not isinstance(fixtures, list):
            self.error("CCSB-T09-NEGATIVE-FIXTURES", "negativeFixtures must be an array.")
            return

        categories = {fixture.get("category") for fixture in fixtures}
        for category in self.manifest.get("requiredNegativeFixtureCategories", []):
            if category not in categories:
                self.error("CCSB-T09-NEGATIVE-COVERAGE", f"Missing negative fixture category {category}.")

        for fixture in fixtures:
            fixture_id = fixture.get("id", "<unknown>")
            entity = fixture.get("entity")
            if entity not in self.catalog["entities"]:
                self.error("CCSB-T09-NEGATIVE-ENTITY", f"{fixture_id} uses unknown entity {entity}.")
            diagnostic = fixture.get("expectedDiagnostic")
            if not isinstance(diagnostic, str) or not diagnostic.startswith("CCSB-T09-"):
                self.error("CCSB-T09-NEGATIVE-DIAGNOSTIC", f"{fixture_id} must use CCSB-T09-* expectedDiagnostic.")
            mutates_record = fixture.get("mutatesRecord")
            if mutates_record and mutates_record not in record_map:
                self.error("CCSB-T09-NEGATIVE-RECORD", f"{fixture_id} mutates unknown record {mutates_record}.")
            removes = fixture.get("removesReferenceField")
            if removes and entity in self.catalog["entities"]:
                if (entity, removes) not in self.catalog["lookupTargets"]:
                    self.error("CCSB-T09-NEGATIVE-LOOKUP", f"{fixture_id} removes unknown lookup {entity}.{removes}.")
            for field_name, value in fixture.get("sets", {}).items():
                field = self.catalog["entities"].get(entity, {}).get("fields", {}).get(field_name)
                if not field:
                    self.error("CCSB-T09-NEGATIVE-FIELD", f"{fixture_id} sets unknown field {entity}.{field_name}.")
                else:
                    self.validate_field_value(fixture_id, entity, field, value)

    def validate_business_rules(self, records: list[dict[str, Any]], record_map: dict[str, dict[str, Any]]) -> None:
        board_versions = [r for r in records if r.get("entity") == "ccsb_boardversion"]
        active_versions = [r for r in board_versions if r.get("attributes", {}).get("ccsb_lifecyclestate") == 831020003]
        if len(active_versions) != 1:
            self.error("CCSB-T09-ACTIVE-VERSION-COUNT", "Exactly one active board version is required.")
        elif not active_versions[0]["attributes"].get("ccsb_isimmutable"):
            self.error("CCSB-T09-ACTIVE-VERSION-IMMUTABLE", "Active board version must be immutable.")
        elif active_versions[0]["attributes"].get("ccsb_validationstatus") != 831020001:
            self.error("CCSB-T09-ACTIVE-VERSION-VALIDATED", "Active board version must have Passed validation.")

        for version in board_versions:
            attrs = version.get("attributes", {})
            if attrs.get("ccsb_lifecyclestate") == 831020000 and attrs.get("ccsb_isimmutable") is not False:
                self.error("CCSB-T09-DRAFT-VERSION-MUTABLE", f"{version['id']} draft version must remain mutable.")

        for board in [r for r in records if r.get("entity") == "ccsb_boardregistry"]:
            active_refs = [ref for ref in board.get("references", []) if ref.get("field") == "ccsb_activeboardversionid"]
            if board.get("attributes", {}).get("ccsb_lifecyclestate") == 831020001 and not active_refs:
                self.error("CCSB-T09-BOARD-ACTIVE-VERSION", f"{board['id']} active board needs active version.")
            for ref in active_refs:
                target = record_map.get(ref["id"])
                if target and target.get("attributes", {}).get("ccsb_lifecyclestate") != 831020003:
                    self.error("CCSB-T09-BOARD-ACTIVE-VERSION", f"{board['id']} active version reference is not Active.")

        for projection in [r for r in records if r.get("entity") == "ccsb_runtimeprojection"]:
            attrs = projection.get("attributes", {})
            if attrs.get("ccsb_iscurrent") and attrs.get("ccsb_projectionstatus") != 831020000:
                self.error("CCSB-T09-STALE-PROJECTION", f"{projection['id']} current projection must be Valid.")
            version_ref = self.find_ref(projection, "ccsb_boardversionid")
            if version_ref:
                target = record_map.get(version_ref["id"])
                if target and target.get("attributes", {}).get("ccsb_lifecyclestate") != 831020003:
                    self.error("CCSB-T09-PROJECTION-ACTIVE-VERSION", f"{projection['id']} must target active version.")

        for item in [r for r in records if r.get("entity") == "ccsb_publishsnapshotitem"]:
            attrs = item.get("attributes", {})
            if attrs.get("ccsb_isimmutable") is not True:
                self.error("CCSB-T09-SNAPSHOT-ITEM-IMMUTABLE", f"{item['id']} must be immutable.")
            if not attrs.get("ccsb_retentionuntil"):
                self.error("CCSB-T09-SNAPSHOT-RETENTION", f"{item['id']} must define retentionuntil.")

        for audit in [r for r in records if r.get("entity") == "ccsb_operationaudit"]:
            attrs = audit.get("attributes", {})
            if not attrs.get("ccsb_recordhash") or not attrs.get("ccsb_previousrecordhash"):
                self.error("CCSB-T09-AUDIT-HASH", f"{audit['id']} must define append-only hash chain fields.")
            if not attrs.get("ccsb_retentionuntil"):
                self.error("CCSB-T09-AUDIT-RETENTION", f"{audit['id']} must define retentionuntil.")

        for change in [r for r in records if r.get("entity") == "ccsb_schedulechange"]:
            attrs = change.get("attributes", {})
            if attrs.get("ccsb_isrollbackcandidate") and not attrs.get("ccsb_rollbackimagejson"):
                self.error("CCSB-T09-ROLLBACK-IMAGE", f"{change['id']} rollback candidate needs rollback image.")

        for lock in [r for r in records if r.get("entity") == "ccsb_publishlock"]:
            attrs = lock.get("attributes", {})
            if attrs.get("ccsb_isactive") and not attrs.get("ccsb_expireson"):
                self.error("CCSB-T09-ACTIVE-LOCK-EXPIRY", f"{lock['id']} active lock needs expireson.")
            if attrs.get("ccsb_isactive") and not attrs.get("ccsb_retentionuntil"):
                self.error("CCSB-T09-LOCK-RETENTION", f"{lock['id']} active lock needs retentionuntil.")

    @staticmethod
    def find_ref(record: dict[str, Any], field: str) -> dict[str, Any] | None:
        for ref in record.get("references", []):
            if ref.get("field") == field:
                return ref
        return None

    def write_report(self, report_path: Path) -> None:
        records = self.manifest.get("records", [])
        fixtures = self.manifest.get("negativeFixtures", [])
        entities = sorted({record.get("entity") for record in records})
        status = "PASS" if not self.issues else "FAIL"
        generated = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        lines = [
            "# US-004-T09 Static Integrity Report",
            "",
            f"**Status:** {status}",
            f"**Generated:** {generated}",
            f"**Manifest:** `{self.manifest_path.relative_to(ROOT).as_posix()}`",
            "",
            "## Counts",
            "",
            f"- Seed records: {len(records)}",
            f"- Entity coverage: {len(entities)} entities",
            f"- Negative fixtures: {len(fixtures)}",
            f"- Errors: {len(self.issues)}",
            f"- Warnings: {len(self.warnings)}",
            "",
            "## Entity Coverage",
            "",
        ]
        lines.extend(f"- `{entity}`" for entity in entities)
        lines.extend(["", "## Validation Scope", ""])
        lines.extend(
            [
                "- Manifest header and fixed clock",
                "- Schema-aligned entities, fields, required fields, types, ranges, and choice values",
                "- Relationship lookup targets and required lookup presence",
                "- Deterministic seed-key uniqueness",
                "- Active board-version lifecycle and immutability",
                "- Current runtime projection validity",
                "- Publish snapshot, audit, lock, rollback, and retention assertions",
                "- Required negative fixture coverage",
                "",
                "## Issues",
                "",
            ]
        )
        if not self.issues and not self.warnings:
            lines.append("- None")
        for issue in self.issues + self.warnings:
            lines.append(f"- [{issue.severity.upper()}] `{issue.code}` - {issue.message}")
        lines.extend(
            [
                "",
                "## Boundary",
                "",
                "This is a static seed-contract validation. Live Dataverse upsert, teardown, credential handling, and CI environment scheduling remain deployment work.",
                "",
            ]
        )
        report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the US-004-T09 deterministic seed manifest.")
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
        f"OK: {len(validator.manifest.get('records', []))} seed records, "
        f"{len(validator.manifest.get('negativeFixtures', []))} negative fixtures, "
        f"{len(validator.warnings)} warning(s)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

