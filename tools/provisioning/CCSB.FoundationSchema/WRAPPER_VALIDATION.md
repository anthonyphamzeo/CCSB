# Wrapper validation record — v1.0.0.2

## Static checks completed

- `run-provisioner.ps1` no longer uses `[CmdletBinding()]`, eliminating the `-WhatIf`
  common-parameter collision.
- The script passes `--what-if` to `Program.cs` when either `-WhatIf` or
  `-ValidateOnly` is supplied.
- The script checks the connection locally before starting a non-validation run and
  produces a clear PowerShell error rather than a later .NET exception.
- Native `dotnet` arguments are assembled in one array and passed using `& dotnet
  @dotnetArguments`, which is compatible with Windows PowerShell 5.1 and PowerShell 7+.
- `Program.cs` still exits before creating `ServiceClient` when it receives
  `--what-if`.

## Expected commands

```powershell
.\run-provisioner.ps1 -WhatIf
.\run-provisioner.ps1 -ValidateOnly
$env:DATAVERSE_CONNECTION_STRING = '<secure connection string>'
.\run-provisioner.ps1
```
