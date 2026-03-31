param(
  [string]$Wav = "skills/tmall-genie-voice-bridge/tmp_audio/listen-once-test.wav",
  [string]$Config = "skills/tmall-genie-voice-bridge/config.local-speaker.json",
  [string]$Python = "python"
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

if (-not [System.IO.Path]::IsPathRooted($Wav)) {
  $Wav = Join-Path (Get-Location).Path $Wav
}
if (-not [System.IO.Path]::IsPathRooted($Config)) {
  $Config = Join-Path (Get-Location).Path $Config
}

$Wav = (Resolve-Path -LiteralPath $Wav).Path
$Config = (Resolve-Path -LiteralPath $Config).Path

$listenPy = Join-Path $skillRoot 'scripts/listen_once.py'
if (-not (Test-Path -LiteralPath $listenPy)) {
  throw "Cannot find scripts/listen_once.py at: $listenPy"
}

& $Python $listenPy --wav $Wav --echo-speak --config $Config
exit $LASTEXITCODE
