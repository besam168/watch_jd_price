param(
    [string]$WindowQuery = "OpenClaw",
    [string]$TextToType = "Desktop automation demo workflow"
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

$lock = Run-Py -ScriptArgs @("set-window-lock", $WindowQuery, "0")
$before = Join-Path $artifactDir ("demo-before-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".png")
& powershell -ExecutionPolicy Bypass -File $capture $before | Out-Null
Run-Py -ScriptArgs @("focus-window", $WindowQuery, "0") | Out-Null
Start-Sleep -Milliseconds 300
$typeResult = Run-Py -ScriptArgs @("type-text", $TextToType)
Start-Sleep -Milliseconds 300
$hotkeyResult = Run-Py -ScriptArgs @("press-hotkey", "ctrl+a")
$after = Join-Path $artifactDir ("demo-after-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".png")
& powershell -ExecutionPolicy Bypass -File $capture $after | Out-Null
$actions = Run-Py -ScriptArgs @("get-recent-actions", "6")
Run-Py -ScriptArgs @("clear-window-lock") | Out-Null

$result = [pscustomobject]@{
    lock = $lock | ConvertFrom-Json
    before = $before
    typeResult = $typeResult
    hotkeyResult = $hotkeyResult
    after = $after
    recentActions = $actions | ConvertFrom-Json
}

$result | ConvertTo-Json -Depth 6
