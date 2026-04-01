$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$demo = Join-Path $root 'demo-http-player-roundtrip.ps1'
$bridgeScript = Join-Path $root 'run-bridge.ps1'
$config = Join-Path $root 'tmp_test_pm/config.mock-http-player.json'
$healthUrl = 'http://127.0.0.1:57881/health'

$bridgeProc = Start-Process -FilePath 'powershell' -ArgumentList @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', $bridgeScript, '-Config', $config) -WorkingDirectory $root -PassThru -WindowStyle Hidden

try {
  $deadline = (Get-Date).AddSeconds(12)
  $healthy = $false
  while ((Get-Date) -lt $deadline) {
    try {
      $resp = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 2
      if ($resp.ok) {
        $healthy = $true
        break
      }
    }
    catch {
    }
    Start-Sleep -Milliseconds 400
  }

  if (-not $healthy) {
    throw 'Bridge did not become healthy in time.'
  }

  $cases = @(
    @{ name = 'ok-200'; args = @('-Text', 'matrix ok') },
    @{ name = 'auth-401'; args = @('-Text', 'matrix auth fail', '-RequireBearer', 'secret-token') },
    @{ name = 'entity-422'; args = @('-Text', 'matrix entity fail', '-RequireEntityId', 'media_player.expected') },
    @{ name = 'server-500'; args = @('-Text', 'matrix server fail', '-ForcedStatus', '500') }
  )

  $results = @()
  foreach ($case in $cases) {
    $raw = & powershell -NoProfile -ExecutionPolicy Bypass -File $demo @($case.args) | Out-String
    $parsed = $null
    try {
      $parsed = $raw | ConvertFrom-Json
    }
    catch {
      $parsed = [pscustomobject]@{ ok = $false; bridge_response = $raw; player_record = $null }
    }

    $results += [pscustomobject]@{
      name = $case.name
      ok = $parsed.ok
      bridge_response = $parsed.bridge_response
      player_record = $parsed.player_record
    }
  }

  $results | ConvertTo-Json -Depth 10
}
finally {
  if ($bridgeProc -and -not $bridgeProc.HasExited) {
    Stop-Process -Id $bridgeProc.Id -Force
  }
}
