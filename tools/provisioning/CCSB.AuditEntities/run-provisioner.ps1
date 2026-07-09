param(
    [string]$EnvironmentUrl = "https://org314f8ab8.crm.dynamics.com",
    [string]$Username,
    [string]$Connection,
    [string]$ExportPath = "out\CSB_AuditEntities_1_0_0_0_unmanaged.zip",
    [switch]$WhatIf,
    [switch]$SkipExport,
    [switch]$SkipMissingRelationshipTargets
)

$ErrorActionPreference = "Stop"

$project = Join-Path $PSScriptRoot "CSB.AuditEntities.Provisioner.csproj"
$arguments = @("run", "--project", $project, "--")

if (-not [string]::IsNullOrWhiteSpace($Connection)) {
    $arguments += @("--connection", $Connection)
}
else {
    $arguments += @("--environment-url", $EnvironmentUrl)
}

if (-not [string]::IsNullOrWhiteSpace($Username)) {
    $arguments += @("--username", $Username)
}

if (-not [string]::IsNullOrWhiteSpace($ExportPath)) {
    $arguments += @("--export", (Join-Path $PSScriptRoot $ExportPath))
}

if ($WhatIf) {
    $arguments += "--what-if"
}

if ($SkipExport) {
    $arguments += "--skip-export"
}

if ($SkipMissingRelationshipTargets) {
    $arguments += "--skip-missing-relationship-targets"
}

Write-Host "Running CSB Audit Entities provisioner..."
& dotnet @arguments
exit $LASTEXITCODE
