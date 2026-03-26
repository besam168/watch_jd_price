---
name: claude-code-bridge
description: Use the local Claude Code CLI as a reusable OpenClaw engineering agent on this Windows machine. Trigger when the user wants Claude Code to analyze a repo, create/review an OpenClaw skill, draft a file, or perform structured coding assistance through local automation.
---

# claude-code-bridge

Use this skill when the user explicitly wants **Claude Code** to do engineering work on the local machine through repeatable workflows.

## What this skill does
- Calls the local `claude` CLI in non-interactive mode
- Supports direct prompts through a base runner
- Supports task-style engineering workflows through a task runner
- Works against the current workspace or a chosen workdir
- Can return plain text, JSON, or save output to files

## Preconditions
Verify Claude Code CLI is available:

```powershell
claude --version
```

If this fails, stop and report that Claude Code CLI is unavailable.

## Scripts
- Base runner: `{baseDir}/scripts/run-claude.ps1`
- Task runner: `{baseDir}/scripts/run-claude-task.ps1`

## Primary workflows

### 1) Direct engineering prompt

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude.ps1 -Workdir "C:\path\to\repo" -Prompt "Summarize the current repo status and suggest next steps."
```

### 2) Analyze a repo or folder

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude-task.ps1 -Task repo-analyze -Workdir "C:\path\to\repo"
```

### 3) Draft a new OpenClaw skill

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude-task.ps1 -Task skill-create -Workdir "C:\path\to\repo" -SkillName "my-skill" -SkillPurpose "Describe what the skill should do"
```

### 4) Review an existing OpenClaw skill

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude-task.ps1 -Task skill-review -Workdir "C:\path\to\repo" -TargetPath "C:\path\to\repo\skills\some-skill"
```

### 5) Draft a project file

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude-task.ps1 -Task file-draft -Workdir "C:\path\to\repo" -DraftFile "SKILL.md"
```

## Supported task templates
- `repo-analyze` — inspect a project and return structure, risks, and next steps
- `skill-create` — produce a practical OpenClaw skill draft
- `skill-review` — review an existing skill for structure and quality issues
- `file-draft` — draft the contents of a named file for the current project

## Recommended usage rules
- Prefer the task runner when the user request matches an existing engineering workflow.
- Prefer the base runner when the user needs a one-off coding or analysis prompt.
- Keep prompts explicit about the target directory, files, and acceptance criteria.
- Use non-interactive Claude CLI automation for reliability; do not promise an interactive Claude terminal unless the user specifically insists on that UI.
- If elevation is needed for a separate system command, handle that in the normal shell flow first.

## Notes
- This skill depends on the local `claude` CLI being installed and authenticated.
- This is a local engineering-agent skill, not an ACP-native Claude harness.
- Current design goal: reliable structured local execution first, more advanced multi-step workflows later.
