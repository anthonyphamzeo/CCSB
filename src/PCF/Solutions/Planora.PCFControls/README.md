# Planora PCF Controls Solution

This folder is reserved for the Dataverse solution project that packages PCF controls.

Create it with Power Platform CLI when the first control is generated:

```powershell
pac solution init --publisher-name CCSB --publisher-prefix ccsb
pac solution add-reference --path ..\..\Controls\Planora.ConfigurationStudio
pac solution add-reference --path ..\..\Controls\Planora.ScheduleBoardRuntime
dotnet build
```

Keep solution output packages out of source control. Store release evidence under `docs/implementation/deployment/`.
