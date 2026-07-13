param(
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'CCSB.Dataverse.EarlyBound\model'),
    [string]$SettingsTemplateFile = (Join-Path $PSScriptRoot 'CCSB.Dataverse.EarlyBound\model\builderSettings.json')
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command pac -ErrorAction SilentlyContinue)) {
    throw 'Power Platform CLI was not found. Install the Microsoft Power Platform CLI or VS Code Power Platform Tools extension first.'
}

if (-not (Test-Path -LiteralPath $SettingsTemplateFile)) {
    throw "Settings file not found: $SettingsTemplateFile"
}

pac modelbuilder build `
    --outdirectory $OutputDirectory `
    --settingsTemplateFile $SettingsTemplateFile
