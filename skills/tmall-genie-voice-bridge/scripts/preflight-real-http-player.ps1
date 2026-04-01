param(
  [string]$ConfigPath = '.\config.home-assistant.example.json',
  [string]$Python = 'python',
  [switch]$NoProbe,
  [int]$Timeout = 3
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Split-Path -Parent $root

if (-not [System.IO.Path]::IsPathRooted($ConfigPath)) {
  $ConfigPath = Join-Path $skillRoot $ConfigPath
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
  throw "Config file not found: $ConfigPath"
}

$configPathResolved = (Resolve-Path -LiteralPath $ConfigPath).Path
$pyScript = Join-Path $root 'preflight_real_http_player.py'
if (-not (Test-Path -LiteralPath $pyScript)) {
  throw "Cannot find preflight_real_http_player.py at: $pyScript"
}

$args = @($pyScript, '--config', $configPathResolved, '--timeout', [string]$Timeout)
if ($NoProbe) {
  $args += '--no-probe'
}

& $Python @args
exit $LASTEXITCODE
