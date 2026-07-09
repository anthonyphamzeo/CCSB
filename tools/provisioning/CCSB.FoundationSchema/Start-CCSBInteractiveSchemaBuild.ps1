<#
.SYNOPSIS
Starts the CCSB foundation schema build using interactive Microsoft Entra OAuth.

.DESCRIPTION
Uses a browser sign-in and a loopback redirect URI (http://localhost). Username is a login hint;
it is not a password and no password is accepted or stored by this script.
#>
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^https://')]
    [string]$EnvironmentUrl,

    [Parameter(Mandatory = $false)]
    [string]$Username,

    [Parameter(Mandatory = $false)]
    [ValidatePattern('^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')]
    [string]$AppId = '51f81489-12ee-4a9e-aaae-a2591f45987d',

    [Parameter(Mandatory = $false)]
    [ValidateSet('http://localhost')]
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

$arguments = @{
    EnvironmentUrl = $EnvironmentUrl
    AppId = $AppId
    RedirectUri = $RedirectUri
    TokenCacheStorePath = $TokenCacheStorePath
    ExportPath = $ExportPath
}

if ($Username) {
    $arguments.Username = $Username
}

if ($CompatibilityReportPath) {
    $arguments.CompatibilityReportPath = $CompatibilityReportPath
}

if ($ExportManaged.IsPresent) {
    $arguments.ExportManaged = $true
}

if ($CoreEntityOverride) {
    $arguments.CoreEntityOverride = $CoreEntityOverride
}

if ($ValidateLiveOnly.IsPresent) {
    $arguments.ValidateLiveOnly = $true
}

if ($SkipExport.IsPresent) {
    $arguments.SkipExport = $true
}

& (Join-Path $ScriptRoot 'run-provisioner.ps1') @arguments
