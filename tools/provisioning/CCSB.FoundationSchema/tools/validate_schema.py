#!/usr/bin/env python3
"""Static validation for the declarative CCSB foundation schema."""
from __future__ import annotations

import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
path = root / 'schema' / 'ccsb.foundation.schema.json'
program_path = root / 'Program.cs'
run_wrapper_path = root / 'run-provisioner.ps1'
interactive_wrapper_path = root / 'Start-CCSBInteractiveSchemaBuild.ps1'
schema = json.loads(path.read_text(encoding='utf-8-sig'))
program = program_path.read_text(encoding='utf-8-sig')
run_wrapper = run_wrapper_path.read_text(encoding='utf-8-sig')
interactive_wrapper = interactive_wrapper_path.read_text(encoding='utf-8-sig')

schema_version = schema.get('schemaVersion')
solution = schema['solution']
tables = schema['tables']
relationships = schema['relationships']
extensions = schema['extensions']
core_entity_aliases = schema.get('coreEntityAliases', [])
relationship_policy = schema.get('relationshipPolicy', {})

version_pattern = re.compile(r'^\d+\.\d+\.\d+(?:\.\d+)?$')
assert schema_version and version_pattern.match(schema_version), 'Invalid schemaVersion'
assert version_pattern.match(solution['version']), 'Invalid solution.version'

assert len(tables) == 14, f"Expected 14 tables, found {len(tables)}"
table_logical_names = {x['logicalName'] for x in tables}
assert len(table_logical_names) == len(tables), 'Duplicate table logical name'
assert 'ccsb_boardregistry' in table_logical_names, 'Foundation Board Registry table missing'
assert 'ccsb_board' not in table_logical_names, 'Foundation schema must not reserve Core ccsb_board'
assert len({x['schemaName'] for x in relationships}) == len(relationships), 'Duplicate relationship schema name'
assert all(x['logicalName'].startswith('ccsb_') for x in tables), 'Invalid table prefix'
assert all(x['schemaName'].startswith('ccsb_') for x in relationships), 'Invalid relationship prefix'
assert all(x['lookupLogicalName'].startswith('ccsb_') for x in relationships), 'Invalid lookup prefix'
assert all(x['lookupLogicalName'].endswith('id') for x in relationships), 'Lookup logical names must end with id'
assert relationship_policy.get('delete') == 'Restrict', 'Delete policy must be Restrict'
assert len({x['canonicalLogicalName'] for x in core_entity_aliases}) == len(core_entity_aliases), 'Duplicate Core entity alias'
assert all(x['canonicalLogicalName'] and x['displayName'] for x in core_entity_aliases), 'Invalid Core entity alias'

valid_types = {'String', 'Memo', 'Choice', 'Boolean', 'Integer', 'Decimal', 'DateOnly', 'DateAndTime'}
for table in tables:
    names = {table['primaryName']['logicalName']}
    for field in table['fields']:
        assert field['logicalName'] not in names, f"Duplicate field {table['logicalName']}.{field['logicalName']}"
        names.add(field['logicalName'])
        assert field['logicalName'].startswith('ccsb_'), f"Invalid field prefix: {field['logicalName']}"
        assert field['type'] in valid_types, f"Unsupported type {field['type']}"
        if field['type'] == 'String':
            assert field.get('maxLength', 200) <= 4000, f"String too long: {field['logicalName']}"
        if field['type'] == 'Memo':
            assert field.get('maxLength', 100000) <= 1048576, f"Memo too long: {field['logicalName']}"
        if field['type'] == 'Choice':
            assert field.get('choiceOptions'), f"Choice missing options: {field['logicalName']}"

for extension in extensions:
    for field in extension['fields']:
        assert field['logicalName'].startswith('ccsb_'), f"Invalid extension field prefix: {field['logicalName']}"
        assert field['type'] in valid_types, f"Unsupported extension type {field['type']}"

known_core_entities = {
    'ccsb_calendar',
    'ccsb_groupnode',
    'ccsb_resource',
    'ccsb_service',
    'ccsb_scheduleitem',
    'ccsb_scheduleboard',
    'ccsb_scheduleversion',
    'ccsb_boardconfiguration',
    'ccsb_eventtypedefinition',
    'ccsb_resourcedefinition',
    'ccsb_groupdefinition',
    'ccsb_viewdefinition',
    'ccsb_ruledefinition',
    'ccsb_statusdefinition',
    'ccsb_statustransition',
    'ccsb_schedulerequirement',
    'ccsb_scheduleassignment',
    'ccsb_publishsnapshot',
}
known_entities = (
    {table['logicalName'] for table in tables}
    | {extension['entityLogicalName'] for extension in extensions}
    | {alias['canonicalLogicalName'] for alias in core_entity_aliases}
    | known_core_entities
)
for relationship in relationships:
    assert relationship['referencedEntity'] in known_entities, (
        f"Relationship {relationship['schemaName']} references unknown target {relationship['referencedEntity']}")
    assert relationship['referencingEntity'] in known_entities, (
        f"Relationship {relationship['schemaName']} references unknown source {relationship['referencingEntity']}")

validation_table = next(table for table in tables if table['logicalName'] == 'ccsb_configurationvalidationresult')
validation_fields = {field['logicalName'] for field in validation_table['fields']}
required_validation_fields = {
    'ccsb_validationrunid',
    'ccsb_validationcode',
    'ccsb_validationcategory',
    'ccsb_severity',
    'ccsb_resultstatus',
    'ccsb_affectedentitylogicalname',
    'ccsb_affectedrecordid',
    'ccsb_affectedfieldlogicalname',
    'ccsb_message',
    'ccsb_detailjson',
    'ccsb_recommendedaction',
    'ccsb_detectedon',
}
missing_validation_fields = required_validation_fields - validation_fields
assert not missing_validation_fields, f"Validation result fields missing: {sorted(missing_validation_fields)}"

board_version_table = next(table for table in tables if table['logicalName'] == 'ccsb_boardversion')
board_version_fields = {field['logicalName']: field for field in board_version_table['fields']}
required_board_version_compatibility_fields = {
    'ccsb_productversion',
    'ccsb_configurationschemaversion',
    'ccsb_migrationstate',
    'ccsb_compatibilitystatus',
}
missing_board_version_compatibility_fields = required_board_version_compatibility_fields - set(board_version_fields)
assert not missing_board_version_compatibility_fields, (
    f"Board version compatibility fields missing: {sorted(missing_board_version_compatibility_fields)}")
assert board_version_fields['ccsb_productversion']['type'] == 'String', 'Board version product version must be String'
assert board_version_fields['ccsb_configurationschemaversion']['type'] == 'String', (
    'Board version configuration schema version must be String')
assert board_version_fields['ccsb_migrationstate']['type'] == 'Choice', 'Board version migration state must be Choice'
assert board_version_fields['ccsb_compatibilitystatus']['type'] == 'Choice', (
    'Board version compatibility status must be Choice')
for value in ('None', 'Pending', 'Running', 'Completed', 'Failed', 'Blocked'):
    assert any(option['label'] == value for option in board_version_fields['ccsb_migrationstate']['choiceOptions']), (
        f"Board version migration state missing option: {value}")

runtime_projection_table = next(table for table in tables if table['logicalName'] == 'ccsb_runtimeprojection')
runtime_projection_fields = {field['logicalName']: field for field in runtime_projection_table['fields']}
required_projection_compatibility_fields = {
    'ccsb_productversion',
    'ccsb_configurationschemaversion',
    'ccsb_projectionschemaversion',
}
missing_projection_compatibility_fields = required_projection_compatibility_fields - set(runtime_projection_fields)
assert not missing_projection_compatibility_fields, (
    f"Runtime projection compatibility fields missing: {sorted(missing_projection_compatibility_fields)}")
for field_name in required_projection_compatibility_fields:
    assert runtime_projection_fields[field_name]['type'] == 'String', (
        f"Runtime projection compatibility field must be String: {field_name}")
assert any(r['schemaName'] == 'ccsb_boardversion_ccsb_configurationvalidationresult' for r in relationships), (
    'Missing board-version validation result relationship')
assert any(r['schemaName'] == 'ccsb_operation_ccsb_configurationvalidationresult' for r in relationships), (
    'Missing operation validation result relationship')
schedule_board_registry_relationship = next(
    (r for r in relationships if r['schemaName'] == 'ccsb_boardregistry_ccsb_scheduleboard'),
    None,
)
assert schedule_board_registry_relationship is not None, 'Missing Schedule Board to Board Registry relationship'
assert schedule_board_registry_relationship['referencedEntity'] == 'ccsb_boardregistry', (
    'Schedule Board registry relationship must target ccsb_boardregistry')
assert schedule_board_registry_relationship['referencingEntity'] == 'ccsb_scheduleboard', (
    'Schedule Board registry relationship must extend ccsb_scheduleboard')
assert schedule_board_registry_relationship['lookupLogicalName'] == 'ccsb_boardregistryid', (
    'Schedule Board registry lookup must avoid ccsb_boardid collision')

live_gate_markers = [
    'ValidateLiveMetadataCompatibility',
    '--validate-live-only',
    '--compatibility-report',
    'CCSB-SCHEMA-FIELD-TYPE-MISMATCH',
    'CCSB-SCHEMA-RELATIONSHIP-CARDINALITY-MISMATCH',
    'CCSB-SCHEMA-SOLUTION-VERSION-MISMATCH',
    'EnsureCoreResolutionDoesNotUseFoundationName',
    'CCSB-SCHEMA-CORE-ENTITY-RESOLUTION-FAILED',
    '--export-managed',
    'ExportManaged',
    'Managed = _options.ExportManaged',
    'CCSB_FoundationSchema_1_0_0_1_managed.zip',
]
for marker in live_gate_markers:
    assert marker in program, f"Implementation marker missing from Program.cs: {marker}"

wrapper_markers = [
    'ExportManaged',
    'CCSB_FoundationSchema_1_0_0_1_managed.zip',
]
for marker in wrapper_markers:
    assert marker in run_wrapper, f"Managed export marker missing from run-provisioner.ps1: {marker}"
    assert marker in interactive_wrapper, f"Managed export marker missing from Start-CCSBInteractiveSchemaBuild.ps1: {marker}"

new_fields = sum(len(t['fields']) + 1 for t in tables)
extension_fields = sum(len(x['fields']) for x in extensions)
print(
    f"OK: schema {schema_version}, {len(tables)} tables, {new_fields} new-table fields, "
    f"{len(relationships)} lookup relationships, {extension_fields} existing-table fields, "
    f"{len(core_entity_aliases)} Core entity alias rule(s), live compatibility gate and managed export present.")