param(
    [Parameter(Mandatory=$true)][ValidateSet('repo-analyze','file-draft','summarize-text','code-review')][string]$Task,
    [string]$Workdir = "",
    [string]$TargetPath = "",
    [string]$DraftFile = "",
    [string]$InputText = "",
    [string]$Model = "",
    [string]$BaseUrl = "",
    [switch]$OpenAICompat,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runGemini = Join-Path $scriptDir 'run-gemini.ps1'

if ([string]::IsNullOrWhiteSpace($Workdir)) {
    $Workdir = (Get-Location).Path
}

switch ($Task) {
    'repo-analyze' {
        $prompt = @"
Analyze the project or folder at '$Workdir'.
Return:
1. What it appears to be
2. Key files or directories
3. Main risks or gaps
4. Concrete next steps
Keep it concise and actionable.
"@
    }
    'file-draft' {
        if ([string]::IsNullOrWhiteSpace($DraftFile)) {
            throw 'file-draft requires -DraftFile'
        }
        $prompt = @"
Draft the file '$DraftFile' for the project at '$Workdir'.
Infer the most useful content from the current project context.
Return only the draft content, ready to save into the file.
"@
    }
    'summarize-text' {
        if ([string]::IsNullOrWhiteSpace($InputText)) {
            throw 'summarize-text requires -InputText'
        }
        $prompt = @"
Summarize the following text in concise Chinese.
Highlight key points, risks, and next actions if relevant.

$InputText
"@
    }
    'code-review' {
        if ([string]::IsNullOrWhiteSpace($TargetPath)) {
            throw 'code-review requires -TargetPath'
        }
        $prompt = @"
Review the code or file at '$TargetPath'.
Return:
1. What it does
2. Main issues or risks
3. Concrete improvement suggestions
Keep it concise and practical.
"@
    }
}

$params = @{
    Prompt = $prompt
}

if (-not [string]::IsNullOrWhiteSpace($Model)) {
    $params.Model = $Model
}
if (-not [string]::IsNullOrWhiteSpace($BaseUrl)) {
    $params.BaseUrl = $BaseUrl
}
if ($OpenAICompat) {
    $params.OpenAICompat = $true
}
if ($Json) {
    $params.Json = $true
}

& $runGemini @params
