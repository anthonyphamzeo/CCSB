# Provisioner Source Validation - v1.0.0.6

Completed static checks:

- Parsed `schema/ccsb.foundation.schema.json` successfully.
- Confirmed schema version `1.0.0` and solution version `1.0.0.1` are versioned contracts.
- Confirmed 14 foundation tables, 228 new-table fields, 52 lookup relationships, 8 V1 extension fields, and one Core-table alias rule.
- Confirmed relationship policy defaults to Delete Restrict and lookup fields use the `ccsb_*id` convention.
- Confirmed `ccsb_configurationvalidationresult` includes run, code, category, severity, result status, affected entity/record/field, message, detail JSON, recommended action, and detected timestamp fields.
- Confirmed board-version and operation relationships exist for validation evidence records.
- Confirmed the provisioner source contains the live metadata compatibility gate, `--validate-live-only`, `--compatibility-report`, field-type diagnostics, relationship-cardinality diagnostics, solution-version diagnostics, and Core/Foundation logical-name collision handling.
- Confirmed the provisioner uses strongly typed SDK requests for entity/attribute metadata, create operations, relationship retrieval, publish, export, and all-entity metadata discovery.
- Confirmed the provisioner has no `EntityFilters.Keys` reference.
- Confirmed PowerShell wrappers forward `-CoreEntityOverride`, `-ValidateLiveOnly`, `-CompatibilityReportPath`, and `-ExportManaged` to the .NET provisioner.
- Confirmed the default unmanaged export filename is `CCSB_FoundationSchema_1_0_0_1_unmanaged.zip` and the default managed export filename is `CCSB_FoundationSchema_1_0_0_1_managed.zip`.
- Ran `dotnet build --no-restore` successfully with 0 warnings and 0 errors.

Not executed in this packaging environment:

- Connected Dataverse validation/provisioning - requires the target DEV environment and an authenticated user.
- Connected managed solution import/activation - belongs to the downstream environment release rehearsal. The local T10 static policy validator covers the managed export switch, policy manifest, and rehearsal gates.