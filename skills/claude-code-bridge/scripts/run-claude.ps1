param(
    [Parameter(Mandatory=$true)][string]$Prompt,
    [string]$Workdir = "",
    [string]$Model = "",
    [string]$OutputFile = "",
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

Push-Location $Workdir
try {
    $output = & $claudeCmd @args 2>&1
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

$text = ($output | Out-String).Trim()

if (-not [string]::IsNullOrWhiteSpace($OutputFile)) {
    $parent = Split-Path -Parent $OutputFile
    if ($parent) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    Set-Content -Path $OutputFile -Value $text -Encoding UTF8
}

if ($Json) {
    [pscustomobject]@{
        ok = ($exitCode -eq 0)
        exitCode = $exitCode
        workdir = $Workdir
        model = $Model
        outputFile = $OutputFile
        text = $text
    } | ConvertTo-Json -Depth 4
} else {
    if ($exitCode -ne 0) {
        Write-Error "Claude command failed with exit code $exitCode`n$text"
        exit $exitCode
    }
    Write-Output $text
}
