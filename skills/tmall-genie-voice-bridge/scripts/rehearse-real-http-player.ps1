param(
  [string]$Config = '.\config.real-http-player.template.json',
  [string]$BridgeUrl = 'http://127.0.0.1:57881/speak',
  [string]$Text = '真实 HTTP 播放联调演练',
  [string]$Python = 'python',
  [int]$Timeout = 20,
  [switch]$SkipProbe,
  [switch]$Force
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$skillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $skillRoot) {
  $skillRoot = (Get-Location).Path
}

$scriptPath = Join-Path $skillRoot 'rehearse_real_http_player.py'
$argsList = @(
  $scriptPath,
  '--config', $Config,
  '--bridge-url', $BridgeUrl,
  '--text', $Text,
  '--timeout', "$Timeout"
)
if ($SkipProbe) {
  $argsList += '--skip-probe'
}
if ($Force) {
  $argsList += '--force'
}

& $Python @argsList
exit $LASTEXITCODE
