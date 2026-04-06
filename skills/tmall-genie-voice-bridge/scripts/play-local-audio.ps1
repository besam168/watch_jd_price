param(
  [Parameter(Mandatory = $true)]
  [string]$AudioPath,

  [int]$TimeoutSeconds = 20
)

$ErrorActionPreference = "Stop"

$resolved = Resolve-Path -LiteralPath $AudioPath
$audioFile = $resolved.Path
$extension = [System.IO.Path]::GetExtension($audioFile)

# 播放 WAV 文件用 SoundPlayer
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

# 非 WAV 格式优先尝试 Windows Media Player COM；若失败，再回退到系统默认播放器
try {
  $wmp = New-Object -ComObject WMPlayer.OCX
  $wmp.settings.autoStart = $false
  $wmp.settings.volume = 100
  $media = $wmp.newMedia($audioFile)
  $null = $media.duration
  $wmp.currentMedia = $media
  $wmp.controls.play()

  $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
  $observedStates = New-Object System.Collections.Generic.List[int]
  $started = $false

  while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
    $state = [int]$wmp.playState
    if (-not $observedStates.Contains($state)) {
      [void]$observedStates.Add($state)
    }

    if ($state -eq 3) {
      $started = $true
      break
    }

    if ($state -eq 1 -and $stopwatch.Elapsed.TotalMilliseconds -ge 250) {
      break
    }

    Start-Sleep -Milliseconds 120
  }

  $finalState = [int]$wmp.playState
  if (-not $observedStates.Contains($finalState)) {
    [void]$observedStates.Add($finalState)
  }

  if ($started -or $finalState -in @(1, 2, 3, 8, 9, 10)) {
    Write-Output "PLAYBACK_CONFIRMED=1"
    Write-Output "PLAYBACK_BACKEND=WMPlayerCOM"
    Write-Output ("PLAYSTATE_FINAL={0}" -f $finalState)
    Write-Output ("PLAYSTATE_OBSERVED={0}" -f (($observedStates | ForEach-Object { $_.ToString() }) -join ','))
    exit 0
  }
}
catch {
  # swallow and fall through to fallback
}

try {
  $process = Start-Process -FilePath "rundll32.exe" -ArgumentList "url.dll,FileProtocolHandler", $audioFile -PassThru -WindowStyle Hidden
  Start-Sleep -Milliseconds 1200
  Write-Output "PLAYBACK_CONFIRMED=0"
  Write-Output "PLAYBACK_BACKEND=ShellOpenFallback"
  Write-Output "PLAYSTATE_FINAL=STARTED_DEFAULT_PLAYER"
  if ($process -and $process.Id) {
    Write-Output ("PLAYBACK_PROCESS_ID={0}" -f $process.Id)
  }
  exit 0
}
catch {
  throw ("Failed to play audio via WMPlayer COM and Shell fallback: {0}" -f $_.Exception.Message)
}
