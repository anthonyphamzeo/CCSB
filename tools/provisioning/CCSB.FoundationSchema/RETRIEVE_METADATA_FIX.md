# v1.0.0.4 metadata retrieval fix

## Failure corrected

Earlier provisioner builds constructed Dataverse metadata requests by creating a generic `OrganizationRequest` and manually populating its `Parameters` collection.

In the target environment, the generic `RetrieveEntity` request was interpreted as a metadata-ID lookup and failed with:

```text
Required field 'MetadataId' is missing for RequestName='RetrieveEntity'
ErrorCode: 0x80040203
```

## Changes

`Program.cs` now uses the strongly typed Dataverse SDK message classes for all metadata actions:

- `RetrieveEntityRequest` / `RetrieveEntityResponse`
- `RetrieveAttributeRequest` / `RetrieveAttributeResponse`
- `CreateEntityRequest`
- `CreateAttributeRequest`
- `CreateOneToManyRequest`
- `CreateEntityKeyRequest`
- `PublishAllXmlRequest`
- `ExportSolutionRequest` / `ExportSolutionResponse`

This makes the request contract explicit and prevents request parameter-name/serialization ambiguity.

## Recovery

The failed run created the unmanaged solution shell before it reached the first table. Do not delete it. Re-run the corrected provisioner with the same environment and it will find the existing unmanaged solution, keep the same unique name, and continue creating the missing metadata.

```powershell
.\Start-CCSBInteractiveSchemaBuild.ps1 `
  -EnvironmentUrl "https://org314f8ab1118.crm.dynamics.com" `
  -Username "xxxxP@08j5f.onmicrosoft.com"
```

The provisioning process is idempotent for tables, attributes, relationships, and alternate keys: existing components are detected and skipped.
