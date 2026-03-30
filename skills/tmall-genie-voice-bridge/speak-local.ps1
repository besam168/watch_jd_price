param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Text,

  [string]$Config,

  [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$skillRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $skillRoot) {
  $skillRoot = (Get-Location).Path
}

if (-not $Config -or [string]::IsNullOrWhiteSpace($Config)) {
  if ($env:TMALL_GENIE_VOICE_BRIDGE_CONFIG -and -not [string]::IsNullOrWhiteSpace($env:TMALL_GENIE_VOICE_BRIDGE_CONFIG)) {
    $Config = $env:TMALL_GENIE_VOICE_BRIDGE_CONFIG
  }
  else {
    $localSpeakerConfig = Join-Path $skillRoot "config.local-speaker.json"
    if (Test-Path -LiteralPath $localSpeakerConfig) {
      $Config = $localSpeakerConfig
    }
    else {
      $Config = Join-Path $skillRoot "config.json"
    }
  }
}

if (-not [System.IO.Path]::IsPathRooted($Config)) {
  $Config = Join-Path $skillRoot $Config
}
$Config = (Resolve-Path -LiteralPath $Config).Path

$speakPy = Join-Path $skillRoot "scripts/speak.py"
if (-not (Test-Path -LiteralPath $speakPy)) {
  throw "Cannot find scripts/speak.py at: $speakPy"
}

& $Python $speakPy $Text --config $Config
$exitCode = $LASTEXITCODE
if ($exitCode -ne 0) {
  exit $exitCode
}
