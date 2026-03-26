param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$Workdir = "",
    [string]$Model = "",
    [string]$OutputFile = "",
    [string]$SystemPrompt = "",
    [string]$AppendSystemPrompt = "",
    [string]$PermissionMode = "",
    [string[]]$AllowedTools = @(),
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($Workdir)) {
    $Workdir = (Get-Location).Path
}

$claudeCmd = (Get-Command claude -ErrorAction Stop).Source

$args = @('-p', $Prompt)

if (-not [string]::IsNullOrWhiteSpace($Model)) {
    $args += @('--model', $Model)
}
if (-not [string]::IsNullOrWhiteSpace($SystemPrompt)) {
    $args += @('--system-prompt', $SystemPrompt)
}
if (-not [string]::IsNullOrWhiteSpace($AppendSystemPrompt)) {
    $args += @('--append-system-prompt', $AppendSystemPrompt)
}
if (-not [string]::IsNullOrWhiteSpace($PermissionMode)) {
    $args += @('--permission-mode', $PermissionMode)
}
if ($AllowedTools.Count -gt 0) {
    $args += @('--allowedTools', ($AllowedTools -join ','))
}

Push-Location $Workdir
try {
    $output = & $claudeCmd @args 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$text = ($output | Out-String).Trim()
$ok = ($exitCode -eq 0)

if (-not [string]::IsNullOrWhiteSpace($OutputFile)) {
    $parent = Split-Path -Parent $OutputFile
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $OutputFile -Value $text -Encoding UTF8
}

if ($Json) {
    [pscustomobject]@{
        ok = $ok
        exitCode = $exitCode
        workdir = $Workdir
        model = $Model
        permissionMode = $PermissionMode
        allowedTools = $AllowedTools
        outputFile = $OutputFile
        text = $text
    } | ConvertTo-Json -Depth 6
} else {
    if (-not $ok) {
        Write-Error "Claude command failed with exit code $exitCode`n$text"
        exit $exitCode
    }
    Write-Output $text
}
