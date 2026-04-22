param(
    [string]$Query,
    [string]$TargetWindow = "",
    [switch]$UseForeground,
    [string]$VerifyQuery = "",
    [string]$VerifyAbsentQuery = "",
    [string]$Lang = "chi_sim+eng",
    [string]$Preprocess = "gray_upscale2x",
    [switch]$VirtualScreen,
    [int]$Retries = 1,
    [int]$RetryDelayMs = 700,
    [int]$VerifyDelayMs = 900,
    [int]$FocusRetries = 2,
    [int]$FocusVerifyDelayMs = 250,
    [switch]$RequireFocusSuccess
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $PSScriptRoot "desktop-input.py"
$capture = Join-Path $PSScriptRoot "screen-capture-compat.ps1"
$ocr = Join-Path $PSScriptRoot "screen-ocr.py"
$artifactDir = Join-Path $root "artifacts"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

if ([string]::IsNullOrWhiteSpace($Query)) {
    throw "-Query is required"
}

function Run-Py {
    param([string[]]$ScriptArgs)
    & python $py @ScriptArgs
}

function Run-OcrJson {
    param([string[]]$OcrArgs)
    $output = & python $ocr @OcrArgs
    return $output | ConvertFrom-Json
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$before = Join-Path $artifactDir ("locked-click-before-" + $stamp + ".png")
$dryOverlay = Join-Path $artifactDir ("locked-click-dry-overlay-" + $stamp + ".png")
$realOverlay = Join-Path $artifactDir ("locked-click-real-overlay-" + $stamp + ".png")
$after = Join-Path $artifactDir ("locked-click-after-" + $stamp + ".png")

$focusResult = $null
$focusVerification = $null
$lockApplied = $false
try {
    if (-not $UseForeground -and -not [string]::IsNullOrWhiteSpace($TargetWindow)) {
        try {
            $focusResult = Run-Py -ScriptArgs @("focus-window-verified", $TargetWindow, "0", "$FocusRetries", "$FocusVerifyDelayMs", "false")
        } catch {
            $focusResult = $_.Exception.Message
        }

        try {
            $focusVerification = $focusResult | ConvertFrom-Json
        } catch {
            $focusVerification = $focusResult
        }

        if ($RequireFocusSuccess -and -not ($focusVerification -is [psobject] -and $focusVerification.ok)) {
            [pscustomobject]@{
                ok = $false
                error = "focus required but failed"
                stopped = $true
                stoppedAt = "focus"
                focusRequired = $true
                inputAttempted = $false
                focusResult = $focusVerification
                lockState = $null
            } | ConvertTo-Json -Depth 8
            exit 1
        }

        Start-Sleep -Milliseconds 400
    }

    $lock = Run-Py -ScriptArgs @("set-window-lock", "", "0", "true") | ConvertFrom-Json
    $lockApplied = $true
    $foregroundBefore = Run-Py -ScriptArgs @("get-foreground-window-info") | ConvertFrom-Json
    & powershell -ExecutionPolicy Bypass -File $capture $before | Out-Null

    $baseOcrArgs = @($before, $Lang, "--query", $Query, "--query-mode", "contains", "--group-by", "auto", "--top-n", "3", "--preprocess", $Preprocess, "--debug-overlay", $dryOverlay)
    $dry = Run-OcrJson -OcrArgs $baseOcrArgs
    $match = $null
    if ($dry.matches -and $dry.matches.Count -gt 0) {
        $match = $dry.matches[0]
    } elseif ($dry.items -and $dry.items.Count -gt 0) {
        $match = $dry.items[0]
    }
    if (-not $match) {
        throw "Dry-run OCR did not find query: $Query"
    }

    $x = [int][math]::Round($match.centerX)
    $y = [int][math]::Round($match.centerY)
    Run-Py -ScriptArgs @("mouse-move", "$x", "$y") | Out-Null
    $clickResult = Run-Py -ScriptArgs @("mouse-click", "left")
    Start-Sleep -Milliseconds $VerifyDelayMs
    & powershell -ExecutionPolicy Bypass -File $capture $after | Out-Null

    $verifyArgs = @($after, $Lang, "--group-by", "auto", "--top-n", "6", "--preprocess", $Preprocess, "--debug-overlay", $realOverlay)
    $verify = Run-OcrJson -OcrArgs $verifyArgs
    $verifyTexts = @()
    if ($verify.items) {
        $verifyTexts = $verify.items | ForEach-Object { [string]$_.normalizedText }
    }
    $present = $null
    $absent = $null
    if (-not [string]::IsNullOrWhiteSpace($VerifyQuery)) {
        $needle = $VerifyQuery.ToLowerInvariant()
        $present = ($verifyTexts | Where-Object { $_ -like "*${needle}*" }).Count -gt 0
    }
    if (-not [string]::IsNullOrWhiteSpace($VerifyAbsentQuery)) {
        $needleAbsent = $VerifyAbsentQuery.ToLowerInvariant()
        $absent = (($verifyTexts | Where-Object { $_ -like "*${needleAbsent}*" }).Count -eq 0)
    }
    $foregroundAfter = Run-Py -ScriptArgs @("get-foreground-window-info") | ConvertFrom-Json
    $recent = Run-Py -ScriptArgs @("get-recent-actions", "8") | ConvertFrom-Json

    $result = [pscustomobject]@{
        ok = $true
        query = $Query
        focusResult = $focusResult
        focusVerification = $focusVerification
        lock = $lock
        foregroundBefore = $foregroundBefore
        before = $before
        dryOverlay = $dryOverlay
        dryMatch = $match
        click = [pscustomobject]@{
            x = $x
            y = $y
            result = $clickResult
        }
        after = $after
        realOverlay = $realOverlay
        verify = [pscustomobject]@{
            verifyQuery = $(if ($VerifyQuery) { $VerifyQuery } else { $null })
            verifyAbsentQuery = $(if ($VerifyAbsentQuery) { $VerifyAbsentQuery } else { $null })
            present = $present
            absent = $absent
            count = $(if ($verify.count) { $verify.count } else { 0 })
            engine = $verify.engine
        }
        foregroundAfter = $foregroundAfter
        recentActions = $recent
    }

    $result | ConvertTo-Json -Depth 8
} finally {
    if ($lockApplied) {
        Run-Py -ScriptArgs @("clear-window-lock") | Out-Null
    }
}
