# v1.0.0.6 Core Entity Resolution Fix

## Fault repaired

Earlier source revisions assumed that the existing V1 **Schedule Board** table had the logical name `ccsb_scheduleboard`. The core table list supplied by the implementation team only confirms the display name **Schedule Board**; a display name is not proof of the logical name.

The DEV environment has shown that the Core **Schedule Board** table can resolve to `ccsb_board`. That logical name conflicted with the original foundation Board registry table name.

## Behaviour in v1.0.0.6

Before the provisioner creates or changes metadata, it now verifies every non-foundation table required by extensions and relationships.

For `ccsb_scheduleboard`, it uses this sequence:

1. Try the exact logical name `ccsb_scheduleboard`.
2. If not found, retrieve custom table metadata and find the unique table whose display name is **Schedule Board**.
3. Use that resolved logical name consistently for extensions and lookup relationships.
4. If the resolved Core logical name is reserved for a foundation table, stop before creating schema components and report a Core/Foundation logical-name collision.
5. If there are no matches or more than one match, stop before creating schema components and print a clear error.

An explicit override is also available when a tenant has duplicate display labels:

```powershell
-CoreEntityOverride 'ccsb_scheduleboard=<actual-logical-name>'
```

The override is validated against Dataverse before use.

## Collision Resolution

The foundation Board registry table now uses `ccsb_boardregistry` instead of `ccsb_board`. The relationship from the Core Schedule Board table to the registry uses lookup field `ccsb_boardregistryid`, so it does not collide with the Core `ccsb_boardid` primary key when the Core Schedule Board table resolves to `ccsb_board`.

## Safe Re-run

The previous execution may already have created some or all foundation tables and some extension columns. Do **not** delete the unmanaged `ccsb_foundationschema` solution. This provisioner is idempotent: it detects existing components and creates only missing components.

The source schema uses solution version `1.0.0.1`; the existing DEV unmanaged solution is updated during the re-run.