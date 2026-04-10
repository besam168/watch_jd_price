param(
    [string]$Url = "http://127.0.0.1:18789/chat?session=main",
    [string]$Message = "继续",
    [int]$WaitAfterOpenMs = 3500,
    [int]$WaitAfterFocusMs = 800,
    [int]$WaitAfterClickMs = 400,
    [int]$WaitAfterTypeMs = 300,
    [int]$WaitAfterSendMs = 2500,
    [switch]$NoOpen
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
$runDir = Join-Path $outputDir "control-continue_$stamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$desktopInput = Join-Path $rootDir 'extensions\desktop-input-control\scripts\desktop-input.py'
$screenOcr = Join-Path $rootDir 'extensions\desktop-input-control\scripts\screen-ocr.py'
$captureScreen = Join-Path $rootDir 'skills\telegram-image-sender\scripts\capture-screen.ps1'

function Invoke-DesktopInput {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )
    $result = & python $desktopInput @Args
    return $result
}

function Capture-Png {
    param(
        [Parameter(Mandatory = $true)]
        [string]$OutPath
    )
    & powershell -ExecutionPolicy Bypass -File $captureScreen | Out-Null
    $latest = Get-ChildItem -Path (Join-Path $rootDir 'skills\telegram-image-sender\output') -Filter '*.png' |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
    if (-not $latest) {
        throw '未找到截图输出文件'
    }
    Copy-Item -Force $latest.FullName $OutPath
    return $OutPath
}

function Run-Ocr {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ImagePath,
        [string]$Query
    )

    $args = @($screenOcr, $ImagePath, 'chi_sim+eng', '--preprocess', 'gray_upscale2x')
    if ($Query) {
        $args += @('--query', $Query)
    }
    $raw = & python @args
    return ($raw -join "`n")
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
        $log.steps += [ordered]@{ step = 'open-url'; result = ($openResult -join "`n") }
        Start-Sleep -Milliseconds $WaitAfterOpenMs
    }

    $focusResult = Invoke-DesktopInput -Args @('focus-window-verified', 'OpenClaw', '0', '3', '400')
    $log.steps += [ordered]@{ step = 'focus-window'; result = ($focusResult -join "`n") }
    Start-Sleep -Milliseconds $WaitAfterFocusMs

    $beforeShot = Join-Path $runDir '01_before.png'
    Capture-Png -OutPath $beforeShot | Out-Null
    $beforeOcr = Run-Ocr -ImagePath $beforeShot -Query '继续'
    Set-Content -Path (Join-Path $runDir '01_before_ocr.json') -Value $beforeOcr -Encoding UTF8
    $log.steps += [ordered]@{ step = 'capture-before'; image = $beforeShot }

    $click1 = Invoke-DesktopInput -Args @('mouse-click', 'left')
    $log.steps += [ordered]@{ step = 'click-input-at-current-position'; result = ($click1 -join "`n") }
    Start-Sleep -Milliseconds $WaitAfterClickMs

    $typeResult = Invoke-DesktopInput -Args @('type-text', $Message)
    $log.steps += [ordered]@{ step = 'type-text'; result = ($typeResult -join "`n") }
    Start-Sleep -Milliseconds $WaitAfterTypeMs

    $sendResult = Invoke-DesktopInput -Args @('press-hotkey', 'enter')
    $log.steps += [ordered]@{ step = 'press-enter'; result = ($sendResult -join "`n") }
    Start-Sleep -Milliseconds $WaitAfterSendMs

    $afterShot = Join-Path $runDir '02_after.png'
    Capture-Png -OutPath $afterShot | Out-Null
    $afterOcr = Run-Ocr -ImagePath $afterShot -Query '继续'
    Set-Content -Path (Join-Path $runDir '02_after_ocr.json') -Value $afterOcr -Encoding UTF8
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
