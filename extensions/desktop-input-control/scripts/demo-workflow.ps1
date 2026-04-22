param(
    [string]$WindowQuery = "",
    [switch]$UseForeground,
    [string]$TextToType = "Desktop automation demo workflow",
    [int]$FocusRetries = 2,
    [int]$FocusVerifyDelayMs = 250,
    [switch]$RequireFocusSuccess
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $PSScriptRoot "desktop-input.py"
$capture = Join-Path $PSScriptRoot "screen-capture-compat.ps1"
$artifactDir = Join-Path $root "artifacts"
New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

function Run-Py {
    param([string[]]$ScriptArgs)
    & python $py @ScriptArgs
}

if (-not $PSBoundParameters.ContainsKey('UseForeground') -and [string]::IsNullOrWhiteSpace($WindowQuery)) {
    $UseForeground = $true
}

$lockApplied = $false
try {
    if ($UseForeground) {
        $lock = Run-Py -ScriptArgs @("set-window-lock", "", "0", "true")
        $lockApplied = $true
    } else {
        $lock = Run-Py -ScriptArgs @("set-window-lock", $WindowQuery, "0", "false")
        $lockApplied = $true

        $focusRaw = $null
        $focusVerification = $null
        try {
            $focusRaw = Run-Py -ScriptArgs @("focus-window-verified", $WindowQuery, "0", "$FocusRetries", "$FocusVerifyDelayMs", "false")
        } catch {
            $focusRaw = $_.Exception.Message
        }

        try {
            $focusVerification = $focusRaw | ConvertFrom-Json
        } catch {
            $focusVerification = $focusRaw
        }

        if ($RequireFocusSuccess -and -not ($focusVerification -is [psobject] -and $focusVerification.ok)) {
            $lockState = if ($lockApplied) { Run-Py -ScriptArgs @("get-window-lock") | ConvertFrom-Json } else { $null }
            [pscustomobject]@{
                ok = $false
                error = "focus required but failed"
                stopped = $true
                stoppedAt = "focus"
                focusRequired = $true
                inputAttempted = $false
                lock = $lock | ConvertFrom-Json
                lockState = $lockState
                focusResult = $focusVerification
            } | ConvertTo-Json -Depth 8
            exit 1
        }
    }

    $before = Join-Path $artifactDir ("demo-before-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".png")
    & powershell -ExecutionPolicy Bypass -File $capture $before | Out-Null
    Start-Sleep -Milliseconds 300
    $typeResult = Run-Py -ScriptArgs @("type-text", $TextToType)
    Start-Sleep -Milliseconds 300
    $hotkeyResult = Run-Py -ScriptArgs @("press-hotkey", "ctrl+a")
    $after = Join-Path $artifactDir ("demo-after-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".png")
    & powershell -ExecutionPolicy Bypass -File $capture $after | Out-Null
    $actions = Run-Py -ScriptArgs @("get-recent-actions", "6")

    $result = [pscustomobject]@{
        lock = $lock | ConvertFrom-Json
        before = $before
        typeResult = $typeResult
        hotkeyResult = $hotkeyResult
        after = $after
        recentActions = $actions | ConvertFrom-Json
    }

    $result | ConvertTo-Json -Depth 6
} finally {
    if ($lockApplied) {
        Run-Py -ScriptArgs @("clear-window-lock") | Out-Null
    }
}
