# US-004-T09 - Data Factory and Integrity Test Suite

## Implementation Summary

US-004-T09 defines the repeatable test-data factory for the CCSB Dataverse foundation schema. The factory should seed one clean reference board registry, one draft board version, one validated/active board version, and deterministic supporting rows for entity mappings, field mappings, relationship mappings, status models, roles, permissions, runtime projections, native schedule items, publish snapshots, publish locks, schedule changes, and resource capabilities.

Seed values must use stable alternate keys, fixed timestamps, predictable names, and synthetic identifiers so CI runs can recreate the same graph without customer data. The suite should load both mapped-source and native-graph variants and confirm that board scope, board-version scope, schedule-version scope, source-record identity, and publish/audit relationships resolve consistently.

Integrity tests must cover key uniqueness, required lookup presence, Delete Restrict relationships, lifecycle transitions, active-version immutability, retention flags, append-only audit/publish records, stale projection rejection, invalid migration defaults, and unsupported cascade paths. Negative fixtures should deliberately attempt duplicate keys, missing required relationships, invalid status transitions, orphaned schedule records, retired board usage, and stale schema/projection versions.

CI acceptance is met when the factory can provision, validate, and tear down the reference dataset in a non-production Dataverse environment; static schema validation passes; live compatibility validation reports no blocking `CCSB-SCHEMA-*` diagnostics; and the seeded dataset becomes reusable evidence for T07 query/performance tests and downstream runtime tests.

## Boundary

This document summarises the T09 implementation target. The actual CI pipeline wiring and environment-specific credentials remain deployment work outside this summary.
