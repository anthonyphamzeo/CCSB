# v1.0.0.5 build repair: Publish and solution export message namespace

## Symptom

The v1.0.0.4 source can fail to compile with errors similar to:

```text
CS0246: The type or namespace name 'PublishAllXmlRequest' could not be found
CS0246: The type or namespace name 'ExportSolutionRequest' could not be found
CS0246: The type or namespace name 'ExportSolutionResponse' could not be found
```

## Cause

These request/response classes are provided by the Dataverse SDK in the `Microsoft.Crm.Sdk.Messages` namespace, not `Microsoft.Xrm.Sdk.Messages`. The `Microsoft.PowerPlatform.Dataverse.Client` package version 1.2.10 already supplies the relevant assembly transitively.

## Repair

`Program.cs` now adds this namespace alias:

```csharp
using CrmSdkMessages = Microsoft.Crm.Sdk.Messages;
```

The publish and export calls use explicit aliases:

```csharp
_service.Execute(new CrmSdkMessages.PublishAllXmlRequest());

var request = new CrmSdkMessages.ExportSolutionRequest
{
    SolutionName = _schema.Solution.UniqueName,
    Managed = false,
};
var response = (CrmSdkMessages.ExportSolutionResponse)_service.Execute(request);
```

This avoids ambiguity with metadata messages that remain in `Microsoft.Xrm.Sdk.Messages`.

## No Dataverse state was changed

This is a source-only compile repair. The existing `ccsb_foundationschema` unmanaged solution created in DEV may be retained. Run the repaired provisioner again; it will continue creating missing schema components and then publish/export the solution.
