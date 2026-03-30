param(
  [Parameter(Position = 0)]
  [string]$Text,

  [ValidateSet('local','bridge')]
  [string]$Mode = 'local',

  [string]$Config,

  [string]$Url = 'http://127.0.0.1:57881/speak',

  [string]$Python = 'python'
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

if (-not $Config -or [string]::IsNullOrWhiteSpace($Config)) {
  $localSpeakerConfig = Join-Path $skillRoot 'config.local-speaker.json'
  if (Test-Path -LiteralPath $localSpeakerConfig) {
    $Config = $localSpeakerConfig
  }
  else {
    $Config = Join-Path $skillRoot 'config.json'
  }
}

if (-not [System.IO.Path]::IsPathRooted($Config)) {
  $Config = Join-Path $skillRoot $Config
}
$Config = (Resolve-Path -LiteralPath $Config).Path

if (-not $Text -or [string]::IsNullOrWhiteSpace($Text)) {
  Write-Host 'Enter text to speak: ' -ForegroundColor Cyan -NoNewline
  $Text = Read-Host
}

if (-not $Text -or [string]::IsNullOrWhiteSpace($Text)) {
  throw 'Text is required.'
}

if ($Mode -eq 'local') {
  $entry = Join-Path $skillRoot 'speak-local.ps1'
  & $entry -Text $Text -Config $Config -Python $Python
  exit $LASTEXITCODE
}

$body = @{ text = $Text } | ConvertTo-Json -Compress
$response = Invoke-RestMethod -Uri $Url -Method Post -ContentType "application/json; charset=utf-8" -Body $body
$response | ConvertTo-Json -Depth 8
