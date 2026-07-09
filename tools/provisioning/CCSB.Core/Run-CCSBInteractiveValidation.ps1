[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^https://.+\.crm\.dynamics\.com/?$")]
    [string]$EnvironmentUrl,

    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$Username,

    [string]$AppId = "51f81489-12ee-4a9e-aaae-a2591f45987d"
)

$ErrorActionPreference = "Stop"

$environmentUrl = $EnvironmentUrl.TrimEnd("/")
$cacheDirectory = Join-Path $env:LOCALAPPDATA "CCSB"
$cacheFile = Join-Path $cacheDirectory "msal_cache.data"
New-Item -ItemType Directory -Force -Path $cacheDirectory | Out-Null

# Intentionally omitted: Integrated Security=true
# We want the browser-based OAuth prompt, not Windows account/SID authentication.
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

& (Join-Path $PSScriptRoot "Build-CCSBCore.ps1") -ConnectionString $connectionString
