param(
    [string]$Url = "http://127.0.0.1:18789/chat?session=main",
    [string]$Message = "go",
    [int]$WaitAfterOpenMs = 3500,
    [int]$WaitAfterFocusMs = 800,
    [int]$WaitAfterClickMs = 400,
    [int]$WaitAfterTypeMs = 300,
    [int]$WaitAfterSendMs = 2500,
    [switch]$NoOpen = $true
)

$ErrorActionPreference = 'Stop'

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$skillDir = Split-Path -Parent $baseDir
$rootDir = Split-Path -Parent (Split-Path -Parent $skillDir)

$outputDir = Join-Path $skillDir 'output'
$logDir = Join-Path $skillDir 'logs'
New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$runDir = Join-Path $outputDir ("control-continue_{0}" -f $stamp)
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$desktopInput = Join-Path $rootDir 'extensions\desktop-input-control\scripts\desktop-input.py'
$pythonExe = 'python'
$captureScreen = Join-Path $rootDir 'skills\telegram-image-sender\scripts\capture-screen.ps1'
$telegramOutputDir = Join-Path $rootDir 'skills\telegram-image-sender\output'

function Invoke-DesktopInput {
    param([string[]]$Args)
    & $pythonExe $desktopInput @Args 2>&1
}

function Invoke-DesktopInputUtf8 {
    param([string[]]$Args)
    $env:PYTHONIOENCODING = 'utf-8'
    & $pythonExe $desktopInput @Args 2>&1
}

function Capture-Png {
    param([string]$OutPath)
    & powershell -ExecutionPolicy Bypass -File $captureScreen | Out-Null
    $latest = Get-ChildItem -Path $telegramOutputDir -Filter '*.png' |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw "screenshot output not found"
    }
    Copy-Item -Force $latest.FullName $OutPath
}

$log = [ordered]@{
    startedAt = (Get-Date).ToString('s')
    url = $Url
    message = $Message
    runDir = $runDir
    steps = @()
}

try {
    if (-not $NoOpen) {
        $openResult = Invoke-DesktopInput -Args @('open-url', $Url)
        $log.steps += [ordered]@{ step = 'open-url'; result = ($openResult | Out-String) }
        Start-Sleep -Milliseconds $WaitAfterOpenMs
    }

    $focusResult = Invoke-DesktopInput -Args @('focus-window-verified', 'OpenClaw', '0', '3', '400')
    $log.steps += [ordered]@{ step = 'focus-window'; result = ($focusResult | Out-String) }
    Start-Sleep -Milliseconds $WaitAfterFocusMs

    $beforeShot = Join-Path $runDir '01_before.png'
    Capture-Png -OutPath $beforeShot
    $log.steps += [ordered]@{ step = 'capture-before'; image = $beforeShot }

    $click1 = Invoke-DesktopInput -Args @('mouse-click', 'left')
    $log.steps += [ordered]@{ step = 'click-input-at-current-position'; result = ($click1 | Out-String) }
    Start-Sleep -Milliseconds $WaitAfterClickMs

    $typeResult = Invoke-DesktopInputUtf8 -Args @('type-text', $Message)
    $log.steps += [ordered]@{ step = 'type-text'; result = ($typeResult | Out-String) }
    Start-Sleep -Milliseconds $WaitAfterTypeMs

    $sendResult = Invoke-DesktopInput -Args @('press-hotkey', 'enter')
    $log.steps += [ordered]@{ step = 'press-enter'; result = ($sendResult | Out-String) }
    Start-Sleep -Milliseconds $WaitAfterSendMs

    $afterShot = Join-Path $runDir '02_after.png'
    Capture-Png -OutPath $afterShot
    $log.steps += [ordered]@{ step = 'capture-after'; image = $afterShot }

    $log.status = 'ok'
    $log.finishedAt = (Get-Date).ToString('s')
}
catch {
    $log.status = 'error'
    $log.error = $_.Exception.Message
    $log.finishedAt = (Get-Date).ToString('s')
}

$logPath = Join-Path $runDir 'run-log.json'
$log | ConvertTo-Json -Depth 8 | Set-Content -Path $logPath -Encoding UTF8
Write-Output $logPath
