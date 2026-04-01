param(
  [Parameter(Position = 0)]
  [string]$Text = 'HTTP player validation request received',

  [string]$BridgeUrl = 'http://127.0.0.1:57881/speak',

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

$tmpDir = Join-Path $skillRoot '.tmp_http_player_demo'
New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
$playerLog = Join-Path $tmpDir 'last-player-request.json'
if (Test-Path -LiteralPath $playerLog) {
  Remove-Item -LiteralPath $playerLog -Force
}

$playerScript = Join-Path $skillRoot 'scripts/mock_http_player.py'
$playerProc = Start-Process -FilePath $Python -ArgumentList @($playerScript, '--host', '127.0.0.1', '--port', '58081', '--output', $playerLog) -WorkingDirectory $skillRoot -PassThru -WindowStyle Hidden

try {
  Start-Sleep -Milliseconds 700

  $body = @{ text = $Text } | ConvertTo-Json -Compress
  $bridgeResponse = Invoke-RestMethod -Uri $BridgeUrl -Method Post -ContentType 'application/json; charset=utf-8' -Body $body

  $deadline = (Get-Date).AddSeconds(5)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $playerLog) {
      break
    }
    Start-Sleep -Milliseconds 200
  }

  if (-not (Test-Path -LiteralPath $playerLog)) {
    throw "Mock HTTP player did not receive any request within timeout."
  }

  $playerRecord = Get-Content -LiteralPath $playerLog -Raw | ConvertFrom-Json
  [pscustomobject]@{
    ok = $true
    bridge_response = $bridgeResponse
    player_record = $playerRecord
    player_log = $playerLog
  } | ConvertTo-Json -Depth 10
}
finally {
  if ($playerProc -and -not $playerProc.HasExited) {
    Stop-Process -Id $playerProc.Id -Force
  }
}
