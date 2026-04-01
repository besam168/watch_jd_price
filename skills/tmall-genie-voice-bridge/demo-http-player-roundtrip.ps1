param(
  [Parameter(Position = 0)]
  [string]$Text = 'HTTP player validation request received',

  [string]$BridgeUrl = 'http://127.0.0.1:57881/speak',

  [string]$Python = 'python',

  [string]$RequireBearer = '',

  [string]$RequireEntityId = '',

  [int]$ForcedStatus = 200,

  [switch]$PassAuthToBridge,

  [string]$BridgeConfigPath = ''
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
$playerArgs = @($playerScript, '--host', '127.0.0.1', '--port', '58081', '--output', $playerLog, '--forced-status', "$ForcedStatus")
if ($RequireBearer) {
  $playerArgs += @('--require-bearer', $RequireBearer)
}
if ($RequireEntityId) {
  $playerArgs += @('--require-entity-id', $RequireEntityId)
}
$playerProc = Start-Process -FilePath $Python -ArgumentList $playerArgs -WorkingDirectory $skillRoot -PassThru -WindowStyle Hidden

$restoreConfig = $false
$backupConfigPath = ''

try {
  if ($PassAuthToBridge -and $BridgeConfigPath -and $RequireBearer) {
    if (-not [System.IO.Path]::IsPathRooted($BridgeConfigPath)) {
      $BridgeConfigPath = Join-Path $skillRoot $BridgeConfigPath
    }
    $BridgeConfigPath = (Resolve-Path -LiteralPath $BridgeConfigPath).Path
    $backupConfigPath = "$BridgeConfigPath.bak"
    Copy-Item -LiteralPath $BridgeConfigPath -Destination $backupConfigPath -Force
    $cfg = Get-Content -LiteralPath $BridgeConfigPath -Raw | ConvertFrom-Json
    if (-not $cfg.http_player) {
      $cfg | Add-Member -NotePropertyName http_player -NotePropertyValue ([pscustomobject]@{})
    }
    if (-not $cfg.http_player.headers) {
      $cfg.http_player | Add-Member -NotePropertyName headers -NotePropertyValue ([pscustomobject]@{})
    }
    $cfg.http_player.headers.Authorization = "Bearer $RequireBearer"
    $cfg | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $BridgeConfigPath -Encoding UTF8
    $restoreConfig = $true
  }

  Start-Sleep -Milliseconds 700

  $body = @{ text = $Text } | ConvertTo-Json -Compress
  try {
    $bridgeResponse = Invoke-RestMethod -Uri $BridgeUrl -Method Post -ContentType 'application/json; charset=utf-8' -Body $body
    $bridgeCallOk = $true
  }
  catch {
    $bridgeResponse = $_.Exception.Message
    $bridgeCallOk = $false
  }

  $deadline = (Get-Date).AddSeconds(5)
  while ((Get-Date) -lt $deadline) {
    if (Test-Path -LiteralPath $playerLog) {
      break
    }
    Start-Sleep -Milliseconds 200
  }

  $playerRecord = $null
  if (Test-Path -LiteralPath $playerLog) {
    $playerRecord = Get-Content -LiteralPath $playerLog -Raw | ConvertFrom-Json
  }

  [pscustomobject]@{
    ok = $bridgeCallOk
    bridge_response = $bridgeResponse
    player_record = $playerRecord
    player_log = $(if (Test-Path -LiteralPath $playerLog) { $playerLog } else { $null })
    require_bearer = $RequireBearer
    require_entity_id = $RequireEntityId
    forced_status = $ForcedStatus
  } | ConvertTo-Json -Depth 10
}
finally {
  if ($restoreConfig -and $backupConfigPath -and (Test-Path -LiteralPath $backupConfigPath)) {
    Move-Item -LiteralPath $backupConfigPath -Destination $BridgeConfigPath -Force
  }
  if ($playerProc -and -not $playerProc.HasExited) {
    Stop-Process -Id $playerProc.Id -Force
  }
}
