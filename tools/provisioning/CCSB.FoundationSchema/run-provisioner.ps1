# Intentionally not an advanced script. In advanced PowerShell scripts, -WhatIf can be
# consumed as a common parameter instead of being passed to the .NET provisioner.
param(
    [Parameter(Mandatory = $false)]
    [string]$ConnectionString,

    [Parameter(Mandatory = $false)]
    [string]$EnvironmentUrl,

    [Parameter(Mandatory = $false)]
    [string]$Username,

    [Parameter(Mandatory = $false)]
    [string]$AppId = '51f81489-12ee-4a9e-aaae-a2591f45987d',

    [Parameter(Mandatory = $false)]
    [string]$RedirectUri = 'http://localhost',

    [Parameter(Mandatory = $false)]
    [string]$TokenCacheStorePath,

    [Parameter(Mandatory = $false)]
    [string]$ExportPath,

    [switch]$ExportManaged,

    [Parameter(Mandatory = $false)]
    [string]$CompatibilityReportPath,

    [Parameter(Mandatory = $false)]
    [string[]]$CoreEntityOverride,

    [Alias('ValidateOnly')]
    [switch]$WhatIf,

    [switch]$ValidateLiveOnly,

    [switch]$SkipExport
)

$ErrorActionPreference = 'Stop'

$ScriptRoot = if (-not [string]::IsNullOrWhiteSpace($PSScriptRoot)) {
    $PSScriptRoot
}
else {
    Split-Path -Parent $MyInvocation.MyCommand.Path
}

if (-not $TokenCacheStorePath) {
    $TokenCacheStorePath = Join-Path $ScriptRoot '.dataverse-token-cache'
}

if (-not $ExportPath) {
    $packageName = if ($ExportManaged.IsPresent) {
        'CCSB_FoundationSchema_1_0_0_1_managed.zip'
    }
    else {
        'CCSB_FoundationSchema_1_0_0_1_unmanaged.zip'
    }
    $ExportPath = Join-Path $ScriptRoot (Join-Path 'out' $packageName)
}

if ($ConnectionString -and $EnvironmentUrl) {
    throw 'Use either -ConnectionString or -EnvironmentUrl, not both.'
}

if (-not $ConnectionString -and -not $EnvironmentUrl) {
    $ConnectionString = $env:DATAVERSE_CONNECTION_STRING
}

$dotnetArguments = @(
    'run',
    '--project', (Join-Path $ScriptRoot 'CCSB.FoundationSchema.Provisioner.csproj'),
    '--',
    '--export', $ExportPath
)

if ($WhatIf.IsPresent) {
    $dotnetArguments += '--what-if'
}

if ($ValidateLiveOnly.IsPresent) {
    $dotnetArguments += '--validate-live-only'
}

if ($CompatibilityReportPath) {
    $dotnetArguments += @('--compatibility-report', $CompatibilityReportPath)
}

if ($ExportManaged.IsPresent) {
    $dotnetArguments += '--export-managed'
}

if ($SkipExport.IsPresent) {
    $dotnetArguments += '--skip-export'
}

foreach ($override in @($CoreEntityOverride)) {
    if (-not [string]::IsNullOrWhiteSpace($override)) {
        $dotnetArguments += @('--core-entity-override', $override)
    }
}

if ($ConnectionString) {
    $dotnetArguments += @('--connection', $ConnectionString)
}
elseif ($EnvironmentUrl) {
    $dotnetArguments += @('--environment-url', $EnvironmentUrl)

    if ($Username) {
        $dotnetArguments += @('--username', $Username)
    }

    if ($AppId) {
        $dotnetArguments += @('--app-id', $AppId)
    }

    if ($RedirectUri) {
        $dotnetArguments += @('--redirect-uri', $RedirectUri)
    }

    if ($TokenCacheStorePath) {
        $dotnetArguments += @('--token-cache-store-path', $TokenCacheStorePath)
    }
}

Push-Location $ScriptRoot
try {
    if ($WhatIf.IsPresent) {
        Write-Host 'Validation mode: the provisioner will not connect to Dataverse or make metadata changes.'
    }
    elseif (-not $ConnectionString -and -not $EnvironmentUrl) {
        throw @'
A Dataverse connection is required to provision the schema.

Use either:
  .\run-provisioner.ps1 -ConnectionString '<Dataverse connection string>'
or
  .\run-provisioner.ps1 -EnvironmentUrl 'https://org.crm.dynamics.com' -Username 'user@tenant.onmicrosoft.com'

If the automatic Schedule Board discovery is ambiguous, add:
  -CoreEntityOverride 'ccsb_scheduleboard=<actual-logical-name>'

For static validation only, use:
  .\run-provisioner.ps1 -WhatIf

For connected metadata compatibility validation without changes, use:
  .\run-provisioner.ps1 -EnvironmentUrl 'https://org.crm.dynamics.com' -Username 'user@tenant.onmicrosoft.com' -ValidateLiveOnly -CompatibilityReportPath 'out\foundation-schema-compatibility.json'
'@
    }

    & dotnet @dotnetArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Provisioner failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
