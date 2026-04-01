param(
  [string]$Config,
  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$skillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $skillRoot) {
  $skillRoot = (Get-Location).Path
}

if (-not $Config -or [string]::IsNullOrWhiteSpace($Config)) {
  if (Test-Path -LiteralPath (Join-Path $skillRoot 'config.example.json')) {
    $Config = Join-Path $skillRoot 'config.example.json'
  }
  else {
    $Config = Join-Path $skillRoot 'config.json'
  }
}

if (-not [System.IO.Path]::IsPathRooted($Config)) {
  $Config = Join-Path $skillRoot $Config
}

if (-not (Test-Path -LiteralPath $Config)) {
  throw "Config file not found: $Config"
}

$Config = (Resolve-Path -LiteralPath $Config).Path
$serverPy = Join-Path $skillRoot 'scripts/bridge_server.py'

if (-not (Test-Path -LiteralPath $serverPy)) {
  throw "Cannot find scripts/bridge_server.py at: $serverPy"
}

& $Python $serverPy --config $Config
exit $LASTEXITCODE