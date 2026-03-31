param(
  [string]$Culture = 'zh-CN'
)

$ErrorActionPreference = 'Stop'

function Get-AudioEndpointSnapshot {
  $items = @()

  try {
    $pnp = Get-Command Get-PnpDevice -ErrorAction SilentlyContinue
    if ($pnp) {
      $items = Get-PnpDevice -Class AudioEndpoint -Status OK -ErrorAction SilentlyContinue |
        Select-Object Class, FriendlyName, InstanceId, Status
    }
  }
  catch {}

  if (-not $items -or $items.Count -eq 0) {
    try {
      $items = Get-CimInstance Win32_SoundDevice -ErrorAction SilentlyContinue |
        Select-Object @{Name='Class';Expression={'SoundDevice'}}, ProductName, Name, DeviceID, Status
    }
    catch {}
  }

  return @($items)
}

$result = [ordered]@{
  ok = $false
  culture = $Culture
  timestamp = (Get-Date).ToString('s')
  recognizer = [ordered]@{
    requested = $Culture
    installed = @()
    available = $false
  }
  microphone = [ordered]@{
    default_input_accessible = $false
    error = $null
  }
  devices = @()
}

try {
  Add-Type -AssemblyName System.Speech

  $installedRecognizers = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
  $result.recognizer.installed = @($installedRecognizers | ForEach-Object { $_.Culture.Name })
  $recognizerInfo = $installedRecognizers | Where-Object { $_.Culture.Name -eq $Culture } | Select-Object -First 1
  if ($recognizerInfo) {
    $result.recognizer.available = $true
  }

  try {
    $engine = if ($recognizerInfo) {
      [System.Speech.Recognition.SpeechRecognitionEngine]::new($recognizerInfo)
    }
    else {
      [System.Speech.Recognition.SpeechRecognitionEngine]::new()
    }

    $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())
    $engine.SetInputToDefaultAudioDevice()
    $result.microphone.default_input_accessible = $true
    $engine.Dispose()
  }
  catch {
    $result.microphone.error = $_.Exception.Message
  }

  $result.devices = @(Get-AudioEndpointSnapshot)
  $result.ok = [bool]($result.recognizer.available -and $result.microphone.default_input_accessible)
}
catch {
  $result.microphone.error = $_.Exception.Message
  $result.devices = @(Get-AudioEndpointSnapshot)
}

$result | ConvertTo-Json -Depth 6
