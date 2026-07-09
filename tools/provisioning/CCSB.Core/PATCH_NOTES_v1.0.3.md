# CCSB Core Generator — Patch Notes v1.0.3

## Fixed .NET 8 compilation error in OAuth redirect validation

### Error corrected

```text
CS1061: 'Uri' does not contain a definition for 'IPAddress'
```

### Root cause

The v1.0.2 validator attempted to use `uri.IPAddress`. `System.Uri` has no `IPAddress` property.

### Correction

The validator now uses the supported .NET API:

```csharp
var isLoopbackHttp =
    uri.Scheme.Equals(Uri.UriSchemeHttp, StringComparison.OrdinalIgnoreCase) &&
    uri.IsLoopback;
```

`Uri.IsLoopback` correctly accepts all intended loopback hosts:

- `http://localhost`
- `http://127.0.0.1`
- `http://[::1]`

No table manifest, Dataverse provisioning logic, or authentication parameters changed.

## Archive layout correction

The `v1.0.3` ZIP stores package contents at the ZIP root. Extract it directly into an empty folder to avoid the accidental double-folder path seen in v1.0.2.
