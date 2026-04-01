param(
  [string]$ConfigPath = '.\config.home-assistant.example.json'
)

$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillRoot = Split-Path -Parent $root

if (-not [System.IO.Path]::IsPathRooted($ConfigPath)) {
  $ConfigPath = Join-Path $skillRoot $ConfigPath
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
  throw "Config file not found: $ConfigPath"
}

$configPathResolved = (Resolve-Path -LiteralPath $ConfigPath).Path
$configData = Get-Content -LiteralPath $configPathResolved -Raw | ConvertFrom-Json

$issues = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$checks = [ordered]@{}

$checks.config = $configPathResolved
$checks.host = $configData.host
$checks.port = $configData.port
$checks.backend = $configData.backend.type
$checks.player_url = $configData.http_player.player_url
$checks.audio_base_url = $configData.http_player.audio_base_url
$checks.public_base_url = $configData.http_player.public_base_url
$checks.entity_id = $configData.http_player.body_template.entity_id
$checks.tts_provider = $configData.tts.provider

if ($configData.backend.type -ne 'local_http_player') {
  $issues.Add("backend.type must be 'local_http_player' for real HTTP playback")
}

$playerUrl = [string]$configData.http_player.player_url
if ([string]::IsNullOrWhiteSpace($playerUrl)) {
  $issues.Add('http_player.player_url is required')
}
elseif ($playerUrl -match 'HOME_ASSISTANT_HOST' -or $playerUrl -match '127\.0\.0\.1' -or $playerUrl -match 'localhost') {
  $warnings.Add('http_player.player_url still looks local or placeholder; verify the playback controller can actually be reached')
}

$authHeader = ''
if ($configData.http_player.headers) {
  $authHeader = [string]$configData.http_player.headers.Authorization
}
if ([string]::IsNullOrWhiteSpace($authHeader)) {
  $warnings.Add('http_player.headers.Authorization is empty')
}
elseif ($authHeader -match 'REPLACE') {
  $issues.Add('http_player.headers.Authorization still contains placeholder text')
}

$entityId = [string]$configData.http_player.body_template.entity_id
if ([string]::IsNullOrWhiteSpace($entityId)) {
  $issues.Add('http_player.body_template.entity_id is required')
}
elseif ($entityId -eq 'media_player.tmall_genie' -or $entityId -match 'REPLACE_ME') {
  $warnings.Add('entity_id is still the example/default value; verify it matches the real target entity')
}

$publicBaseUrl = [string]$configData.http_player.public_base_url
$audioBaseUrl = [string]$configData.http_player.audio_base_url
if ([string]::IsNullOrWhiteSpace($publicBaseUrl) -and [string]::IsNullOrWhiteSpace($audioBaseUrl)) {
  $issues.Add('set http_player.public_base_url or audio_base_url so the playback target can fetch /audio/...')
}
if (-not [string]::IsNullOrWhiteSpace($publicBaseUrl) -and ($publicBaseUrl -match 'BRIDGE_HOST' -or $publicBaseUrl -match 'YOUR_BRIDGE_PUBLIC_HOST' -or $publicBaseUrl -match '127\.0\.0\.1' -or $publicBaseUrl -match 'localhost')) {
  $warnings.Add('http_player.public_base_url still looks placeholder/local; remote players usually cannot fetch audio from it')
}
if (($audioBaseUrl -eq 'auto') -and (($configData.host -eq '127.0.0.1') -or ($configData.host -eq 'localhost'))) {
  $warnings.Add("audio_base_url='auto' depends on the incoming host; if the bridge is only bound locally, remote playback will fail")
}

$bridgeReachability = $null
try {
  $healthUrl = ("http://{0}:{1}/health" -f $configData.host, $configData.port)
  $health = Invoke-WebRequest -UseBasicParsing -Uri $healthUrl -TimeoutSec 3
  $bridgeReachability = [ordered]@{ ok = $true; status_code = [int]$health.StatusCode; url = $healthUrl }
}
catch {
  $bridgeReachability = [ordered]@{ ok = $false; error = $_.Exception.Message }
  $warnings.Add('bridge health endpoint not reachable right now; start the bridge before real testing')
}
$checks.bridge_health = $bridgeReachability

$playerReachability = $null
if (-not [string]::IsNullOrWhiteSpace($playerUrl) -and -not ($playerUrl -match 'HOME_ASSISTANT_HOST') -and -not ($playerUrl -match 'YOUR_PLAYER_HOST')) {
  try {
    $uri = [System.Uri]$playerUrl
    $baseUrl = $uri.Scheme + '://' + $uri.Authority
    $probe = Invoke-WebRequest -UseBasicParsing -Uri $baseUrl -Method Get -TimeoutSec 3
    $playerReachability = [ordered]@{ ok = $true; status_code = [int]$probe.StatusCode; base = $baseUrl }
  }
  catch {
    $playerReachability = [ordered]@{ ok = $false; base = $baseUrl; error = $_.Exception.Message }
    $warnings.Add('playback target base URL did not answer a quick probe; confirm host, port, firewall, and reverse proxy')
  }
}
$checks.player_probe = $playerReachability

$result = [ordered]@{
  ok = ($issues.Count -eq 0)
  issues = @($issues)
  warnings = @($warnings)
  checks = $checks
}

$result | ConvertTo-Json -Depth 8
