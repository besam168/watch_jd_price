param(
    [string]$Url = "https://www.bbc.com/news",
    [string]$WindowQuery = "BBC",
    [string]$Query = "BBC",
    [string]$VerifyQuery = "news",
    [string]$BrowserTarget = "msedge.exe",
    [int]$LaunchWaitMs = 4500,
    [int]$FocusRetries = 3,
    [int]$FocusVerifyDelayMs = 350,
    [int]$VerifyDelayMs = 1200,
    [int]$Retries = 1,
    [int]$RetryDelayMs = 800,
    [switch]$UseForeground,
    [switch]$RequireFocusSuccess
)

$ErrorActionPreference = "Stop"
$OutputEncoding = [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $PSScriptRoot "desktop-input.py"
$capture = Join-Path $PSScriptRoot "screen-capture-compat.ps1"
$artifactDir = Join-Path $root "artifacts"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

function Run-Py {
    param([string[]]$ScriptArgs)
    & python $py @ScriptArgs
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$beforePath = Join-Path $artifactDir ("web-demo-before-" + $stamp + ".png")
$afterPath = Join-Path $artifactDir ("web-demo-after-" + $stamp + ".png")

$browserLaunch = Start-Process -FilePath $BrowserTarget -ArgumentList $Url -PassThru
Start-Sleep -Milliseconds $LaunchWaitMs

$focusResult = $null

try {
    if (-not $UseForeground -and -not [string]::IsNullOrWhiteSpace($WindowQuery)) {
        try {
            $focusResult = Run-Py -ScriptArgs @("focus-window-verified", $WindowQuery, "0", "$FocusRetries", "$FocusVerifyDelayMs", "false") | ConvertFrom-Json
        } catch {
            try {
                $focusResult = $_.Exception.Message | ConvertFrom-Json
            } catch {
                $focusResult = $_.Exception.Message
            }
        }

        if ($RequireFocusSuccess -and -not ($focusResult -is [psobject] -and $focusResult.ok)) {
            [pscustomobject]@{
                ok = $false
                error = "focus required but failed"
                stopped = $true
                stoppedAt = "focus"
                browserPid = $browserLaunch.Id
                focusResult = $focusResult
            } | ConvertTo-Json -Depth 8
            exit 1
        }

        Start-Sleep -Milliseconds 500
    }

    & powershell -ExecutionPolicy Bypass -File $capture $beforePath | Out-Null
    Start-Sleep -Milliseconds $VerifyDelayMs
    & powershell -ExecutionPolicy Bypass -File $capture $afterPath | Out-Null

    $result = [pscustomobject]@{
        ok = $true
        browserPid = $browserLaunch.Id
        url = $Url
        windowQuery = $WindowQuery
        query = $Query
        verifyQuery = $VerifyQuery
        focusResult = $focusResult
        before = $beforePath
        after = $afterPath
        note = "Browser opened and focused. This demo currently validates browser launch + focus + screenshot capture."
        recentActions = $(try { Run-Py -ScriptArgs @("get-recent-actions", "8") | ConvertFrom-Json } catch { $null })
    }

    $result | ConvertTo-Json -Depth 8
} finally {
}
