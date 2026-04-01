param(
  [Parameter(Mandatory = $true)]
  [string]$Config,
  [string]$PreflightJsonPath = '',
  [string]$PreflightJsonInline = '',
  [string]$RehearsalJsonPath = '',
  [string]$RehearsalJsonInline = '',
  [switch]$HumanHeard,
  [string]$HumanNote = '',
  [string]$OutputDir = '.\acceptance_records',
  [ValidateSet('json', 'markdown', 'both')]
  [string]$Format = 'both',
  [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pyScript = Join-Path $scriptRoot 'record_acceptance_result.py'
if (-not (Test-Path -LiteralPath $pyScript)) {
  throw "Cannot find record_acceptance_result.py at: $pyScript"
}

$argsList = @(
  $pyScript,
  '--config', $Config,
  '--human-note', $HumanNote,
  '--output-dir', $OutputDir,
  '--format', $Format
)

if ($PreflightJsonPath) {
  $argsList += @('--preflight-json-path', $PreflightJsonPath)
}
if ($PreflightJsonInline) {
  $argsList += @('--preflight-json-inline', $PreflightJsonInline)
}
if ($RehearsalJsonPath) {
  $argsList += @('--rehearsal-json-path', $RehearsalJsonPath)
}
if ($RehearsalJsonInline) {
  $argsList += @('--rehearsal-json-inline', $RehearsalJsonInline)
}
if ($HumanHeard) {
  $argsList += '--human-heard'
}

& $Python @argsList
exit $LASTEXITCODE
