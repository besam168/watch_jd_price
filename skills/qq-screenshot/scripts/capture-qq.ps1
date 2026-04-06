param(
    [string]$OutputDir = "C:\Users\besam\.openclaw\workspace\qq-screenshots",
    [switch]$NoMedia,
    [ValidateSet('system','pil')]
    [string]$Method = 'pil'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputPath = Join-Path $OutputDir "qq-screenshot_$timestamp.png"

$telegramCaptureScript = "C:\Users\besam\.openclaw\workspace\skills\telegram-image-sender\scripts\capture-screen.ps1"
$liveCaptureScript = "C:\Users\besam\.openclaw\workspace\skills\telegram-live-screenshot\scripts\capture-live.ps1"

function Invoke-PilFallback {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $liveCaptureScript -Method pil -OutputDir $OutputDir -NoMedia | Out-Null
    $latest = Get-ChildItem -Path $OutputDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $latest) {
        throw "PIL screenshot did not produce an output file."
    }
    if ($latest.FullName -ne $outputPath) {
        Copy-Item -LiteralPath $latest.FullName -Destination $outputPath -Force
    }
}

if ($Method -eq 'system') {
    $screenshotsDir = Join-Path $env:USERPROFILE "Pictures\Screenshots"
    $baselineTicks = 0
    if (Test-Path $screenshotsDir) {
        $before = Get-ChildItem $screenshotsDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($before) {
            $baselineTicks = $before.LastWriteTimeUtc.Ticks
        }
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $telegramCaptureScript -UseSystemScreenshot -OutputPath $outputPath | Out-Null

    $copiedOk = $false
    if (Test-Path $outputPath) {
        try {
            $copiedItem = Get-Item $outputPath
            if ($copiedItem.Length -gt 0) {
                if (-not (Test-Path $screenshotsDir)) {
                    $copiedOk = $true
                } else {
                    $after = Get-ChildItem $screenshotsDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                    if ($after -and $after.LastWriteTimeUtc.Ticks -gt $baselineTicks) {
                        $copiedOk = $true
                    }
                }
            }
        } catch {
            $copiedOk = $false
        }
    }

    if (-not $copiedOk) {
        if (Test-Path $outputPath) {
            Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
        }
        Invoke-PilFallback
    }
} else {
    Invoke-PilFallback
}

if (-not (Test-Path $outputPath)) {
    throw "Screenshot file was not created: $outputPath"
}

if ($NoMedia) {
    Write-Output $outputPath
} else {
    Write-Output "MEDIA:$outputPath"
}
