[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^https://.+\.crm\.dynamics\.com/?$")]
    [string]$EnvironmentUrl,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Username,

    [string]$AppId = "51f81489-12ee-4a9e-aaae-a2591f45987d",

    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$environmentUrl = $EnvironmentUrl.TrimEnd("/")
$cacheDirectory = Join-Path $env:LOCALAPPDATA "CCSB"
$cacheFile = Join-Path $cacheDirectory "msal_cache.data"
New-Item -ItemType Directory -Force -Path $cacheDirectory | Out-Null

# Deliberately no Integrated Security=true. That mode asks the SDK to resolve the
# local Windows account and is not suitable for local/Azure AD/consumer Windows profiles
# where the Windows SID cannot be mapped to an account name.
$connectionString = @(
    "AuthType=OAuth"
    "Username=$Username"
    "Url=$environmentUrl"
    "AppId=$AppId"
    "RedirectUri=http://localhost"
    "TokenCacheStorePath=$cacheFile"
    "LoginPrompt=Always"
    "RequireNewInstance=true"
) -join ";"

$runner = Join-Path $PSScriptRoot "Build-CCSBCore.ps1"

if ($Apply) {
    & $runner -ConnectionString $connectionString -Apply
}
else {
    & $runner -ConnectionString $connectionString
}
