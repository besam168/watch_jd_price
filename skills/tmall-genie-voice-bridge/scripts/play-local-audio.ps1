param(
  [Parameter(Mandatory = $true)]
  [string]$AudioPath,

  [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = "Stop"

$resolved = Resolve-Path -LiteralPath $AudioPath
$audioFile = $resolved.Path
$extension = [System.IO.Path]::GetExtension($audioFile)

if ($extension -and $extension.Equals(".wav", [System.StringComparison]::OrdinalIgnoreCase)) {
  try {
    $player = New-Object System.Media.SoundPlayer $audioFile
    $player.Load()
    $player.PlaySync()

    Write-Output "PLAYBACK_CONFIRMED=1"
    Write-Output "PLAYBACK_BACKEND=SoundPlayer"
    Write-Output "PLAYSTATE_FINAL=WAV_SYNC_OK"
    exit 0
  }
  catch {
    throw ("SoundPlayer failed for WAV file: {0}" -f $_.Exception.Message)
  }
}

$terminalStates = @(1, 8)
$observedStates = New-Object System.Collections.Generic.List[int]
$started = $false
$completed = $false
$finalState = $null

$player = $null
try {
  $player = New-Object -ComObject WMPlayer.OCX
  $player.settings.autoStart = $false
  $player.URL = $audioFile
  $player.controls.play()

  # Phase 1: require evidence that playback actually started.
  $startupDeadline = [DateTime]::UtcNow.AddSeconds(8)
  while ([DateTime]::UtcNow -lt $startupDeadline) {
    $state = [int]$player.playState
    $observedStates.Add($state)
    $finalState = $state

    if ($state -eq 3) {
      $started = $true
      break
    }
    if ($state -eq 10) {
      throw "Windows Media Player failed to open media (state=10)."
    }

    Start-Sleep -Milliseconds 200
  }

  if (-not $started) {
    # Very short clips can complete before state=3 is sampled.
    if ($observedStates -contains 1 -or $observedStates -contains 8) {
      $completed = $true
    }
    else {
      throw ("Playback did not reach playing state within startup window. FinalState={0}; Observed={1}" -f $finalState, ($observedStates -join ","))
    }
  }

  # Phase 2: if playback started, wait for completion signal.
  if ($started) {
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
      $state = [int]$player.playState
      $observedStates.Add($state)
      $finalState = $state

      if ($state -in $terminalStates) {
        $completed = $true
        break
      }
      if ($state -eq 10) {
        throw "Windows Media Player failed during playback (state=10)."
      }

      Start-Sleep -Milliseconds 250
    }
  }

  if (-not $completed) {
    throw ("Playback timeout after {0}s. FinalState={1}; Observed={2}" -f $TimeoutSeconds, $finalState, ($observedStates -join ","))
  }

  Write-Output "PLAYBACK_CONFIRMED=1"
  Write-Output ("PLAYSTATE_FINAL={0}" -f $finalState)
  Write-Output ("PLAYSTATE_OBSERVED={0}" -f ($observedStates -join ","))
}
catch {
  Write-Error $_
  exit 1
}
finally {
  if ($player) {
    try { $player.controls.stop() } catch {}
    try { $player.close() } catch {}
  }
}
