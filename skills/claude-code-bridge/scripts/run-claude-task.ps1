param(
    [Parameter(Mandatory=$true)][ValidateSet('repo-analyze','skill-create','skill-review','file-draft')][string]$Task,
    [string]$Workdir = "",
    [string]$TargetPath = "",
    [string]$SkillName = "",
    [string]$SkillPurpose = "",
    [string]$DraftFile = "",
    [string]$Model = "",
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runClaude = Join-Path $scriptDir 'run-claude.ps1'

if ([string]::IsNullOrWhiteSpace($Workdir)) {
    $Workdir = (Get-Location).Path
}

switch ($Task) {
    'repo-analyze' {
        $prompt = @"
Analyze this repository or folder from an engineering perspective.
Return:
1. What it appears to be
2. Key files or directories
3. Main risks or gaps
4. Concrete next steps
Keep it concise and actionable.
"@
    }
    'skill-create' {
        if ([string]::IsNullOrWhiteSpace($SkillName) -or [string]::IsNullOrWhiteSpace($SkillPurpose)) {
            throw 'skill-create requires -SkillName and -SkillPurpose'
        }
        $prompt = @"
Create a concise OpenClaw skill draft for the skill name '$SkillName'.
Purpose: $SkillPurpose
Return:
1. Recommended folder structure
2. A draft SKILL.md
3. Suggested scripts/references if needed
Keep it practical and implementation-oriented.
"@
    }
    'skill-review' {
        if ([string]::IsNullOrWhiteSpace($TargetPath)) {
            throw 'skill-review requires -TargetPath'
        }
        $prompt = @"
Review the OpenClaw skill located at '$TargetPath'.
Return:
1. Structure issues
2. Trigger/description issues
3. Missing files or over-documentation
4. Concrete improvement suggestions
Keep it concise.
"@
    }
    'file-draft' {
        if ([string]::IsNullOrWhiteSpace($DraftFile)) {
            throw 'file-draft requires -DraftFile'
        }
        $prompt = @"
Draft the file '$DraftFile' for this project.
Infer the most useful content from the current workspace context.
Return only the draft content, ready to save into the file.
"@
    }
}

$params = @{
    Prompt = $prompt
    Workdir = $Workdir
}

if (-not [string]::IsNullOrWhiteSpace($Model)) {
    $params.Model = $Model
}
if ($Json) {
    $params.Json = $true
}

& $runClaude @params
