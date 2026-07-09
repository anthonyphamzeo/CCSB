# Foundation Schema Decisions

## Create these tables now

The schema should be created now because it is foundational to the product's configuration-driven, packageable architecture. It prevents later breaking changes to board identity, immutable configuration versions, customer-table mappings, named roles, permissions, runtime projections, validation evidence, and long-running operations.

## Board versus Schedule Board

`ccsb_boardregistry` is not a duplicate of `ccsb_scheduleboard`.

- `ccsb_boardregistry` is the stable product configuration identity. This avoids colliding with Core environments where the operational Schedule Board table resolves to `ccsb_board`.
- `ccsb_boardversion` is the immutable configuration version that controls mappings, definitions, rules, groups, statuses, roles, permissions, and views.
- `ccsb_scheduleboard` is the operational board record used by the scheduling runtime.
- `ccsb_scheduleversion` is the business schedule/release version and is not a substitute for immutable configuration versioning.

## Migration safety

Every new relationship added to an existing V1 table is optional at metadata level. This means existing records remain valid immediately after import. The product must create migration records and enforce the business-required links only when a board configuration is activated or a schedule is published.

## Data ownership and security

All foundation tables are user-owned to retain Dataverse business-unit and ownership-based security options. `ccsb_permissionprofile` and `ccsb_permissionassignment` do not bypass Dataverse security roles. They describe product scope and must be evaluated in addition to Dataverse access checks and Custom API authorization.

## Projection and operations

`ccsb_runtimeprojection` is intentionally a read-only materialized projection. It must be rebuilt from normalized configuration and cannot be used as the source of truth. `ccsb_operation` and `ccsb_operationitem` provide evidence, correlation, retry control, and support visibility for validation, projection generation, publish, rollback, and other lifecycle actions.
