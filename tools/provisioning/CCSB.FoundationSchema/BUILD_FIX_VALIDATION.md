# CCSB Foundation Schema Provisioner — Build Fix Validation

## Fixed compiler error

`EntityFilters.Keys` is not defined by the Dataverse SDK `EntityFilters` enum.

## Code change

`EnsureAlternateKey` now uses `EntityFilters.All` when retrieving metadata for alternate-key discovery. It reads `EntityMetadata.Keys` through a null-safe local collection.

## Static validation completed

- Confirmed `EntityFilters.Keys` no longer appears anywhere in the source package.
- Confirmed all remaining `EntityFilters` usages are `Entity`, `All`, or supplied as a method parameter.
- Confirmed `Program.cs` contains the corrected alternate-key block.
- Confirmed the source ZIP contains no build output folders.

## Build execution note

The packaging environment does not have the .NET SDK installed, so a local `dotnet build` could not be run here. The correction addresses the exact compiler error reported from your Windows build.
