[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ConnectionString,

    [switch]$Apply,

    [string]$OutputPath = (Join-Path $PSScriptRoot "artifacts\CCSB_Core_1_0_0_0_unmanaged.zip"),

    [string]$ManifestPath = (Join-Path $PSScriptRoot "table-manifest.json"),

    [string]$ReportPath = (Join-Path $PSScriptRoot "artifacts\CCSB_Core_build_report.json"),

    [switch]$NoExport
)


$ErrorActionPreference = "Stop"

function Get-ConnectionStringValue {
    param(
        [Parameter(Mandatory = $true)][string]$InputConnectionString,
        [Parameter(Mandatory = $true)][string]$Key
    )

    foreach ($part in $InputConnectionString.Split(';', [System.StringSplitOptions]::RemoveEmptyEntries)) {
        $index = $part.IndexOf('=')
        if ($index -le 0) {
            continue
        }

        $candidateKey = $part.Substring(0, $index).Trim()
        if ($candidateKey.Equals($Key, [System.StringComparison]::OrdinalIgnoreCase)) {
            return $part.Substring($index + 1).Trim()
        }
    }

    return $null
}

$authType = Get-ConnectionStringValue -InputConnectionString $ConnectionString -Key "AuthType"
$redirectUri = Get-ConnectionStringValue -InputConnectionString $ConnectionString -Key "RedirectUri"
$integratedSecurity = Get-ConnectionStringValue -InputConnectionString $ConnectionString -Key "Integrated Security"

if ($integratedSecurity -and $integratedSecurity.Equals("true", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw @"
Integrated Security=true is not supported by this CCSB interactive provisioner.

It makes the Dataverse SDK use the current Windows identity. Your reported
MSAL error, get_user_name_failed / Win32Exception 1332, means that Windows could
not resolve that identity from its SID.

Remove this parameter completely and use:
  AuthType=OAuth;Username=your.name@yourtenant.com;...;LoginPrompt=Always

The included Start-CCSBInteractiveBuild.ps1 in v1.0.4 already uses the correct form.
"@
}

if ($authType -and $authType.Equals("OAuth", [System.StringComparison]::OrdinalIgnoreCase)) {
    if ([string]::IsNullOrWhiteSpace($redirectUri)) {
        throw "OAuth requires RedirectUri=http://localhost for this .NET 8 provisioner."
    }

    if ($redirectUri -match '^(?i:app)://') {
        throw @"
RedirectUri '$redirectUri' is incompatible with this .NET 8/MSAL system-browser flow.

Use:
  RedirectUri=http://localhost

For a tenant-specific app registration, configure the exact same http://localhost value under:
Microsoft Entra ID > App registrations > [your app] > Authentication.

Do not use the model-driven app ID from the Dynamics URL as AppId.
"@
    }

    if ($redirectUri -notmatch '^(?i:http)://(localhost|127\.0\.0\.1|::1)(:\d+)?/?$') {
        throw "RedirectUri '$redirectUri' must be a loopback HTTP URI for this provisioner. Use http://localhost or http://localhost:<port>."
    }
}

$projectPath = Join-Path $PSScriptRoot "src\CCSB.Core.Provisioner.csproj"

if (-not (Get-Command dotnet -ErrorAction SilentlyContinue)) {
    throw ".NET SDK 8 is required. Install it from https://dotnet.microsoft.com/download/dotnet/8.0."
}

if (-not (Test-Path $projectPath)) {
    throw "Provisioner project was not found: $projectPath"
}

$arguments = @(
    "run",
    "--project", $projectPath,
    "--",
    "--connection-string", $ConnectionString,
    "--output", $OutputPath,
    "--manifest", $ManifestPath,
    "--report", $ReportPath
)

if ($Apply) {
    $arguments += "--apply"
}
else {
    $arguments += "--validate-only"
}

if ($NoExport) {
    $arguments += "--no-export"
}

Write-Host "CCSB Core provisioner mode: $(if ($Apply) { 'Apply' } else { 'Validate only' })"
& dotnet @arguments

if ($LASTEXITCODE -ne 0) {
    throw "CCSB Core provisioner failed with exit code $LASTEXITCODE."
}

if ($Apply -and -not $NoExport) {
    Write-Host ""
    Write-Host "Importable unmanaged solution created at:"
    Write-Host $OutputPath
    Write-Host ""
    Write-Host "Build report created at:"
    Write-Host $ReportPath
}
