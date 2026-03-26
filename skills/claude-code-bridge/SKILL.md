---
name: claude-code-bridge
description: Use the local Claude Code CLI from OpenClaw workflows. Trigger when the user asks to run Claude Code, have Claude Code analyze/code in a workspace, draft files via Claude, or build a skill/tool through Claude Code on this Windows machine.
---

# claude-code-bridge

Use this skill when the user explicitly wants **Claude Code** to do coding or analysis work on the local machine.

## What this skill does
- Calls the locally installed `claude` CLI in non-interactive mode
- Runs it against the current workspace or a chosen workdir
- Returns plain text output or writes the result into a file

## Preconditions
Before using this skill, verify:

```powershell
claude --version
```

If that fails, stop and report that Claude Code CLI is not installed or not on PATH.

## Primary workflow

### 1) Quick one-shot Claude Code call

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude.ps1 -Prompt "Summarize the current repo status and suggest next steps." 
```

### 2) Run Claude Code in a specific workspace

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude.ps1 -Workdir "C:\path\to\repo" -Prompt "Create a minimal OpenClaw skill for ..."
```

### 3) Save Claude output to a file

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude.ps1 -Workdir "C:\path\to\repo" -Prompt "Draft a SKILL.md for ..." -OutputFile "C:\path\to\draft.txt"
```

### 4) Machine-readable result

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-claude.ps1 -Prompt "Reply with exactly CLAUDE_OK" -Json
```

## Recommended usage rules
- Prefer short, explicit prompts with concrete file targets and acceptance criteria.
- Use Claude Code for substantial coding or codebase analysis tasks, not for trivial echo-like work.
- If the user asks for an interactive Claude terminal session, explain that this skill uses the **non-interactive CLI path** for reliable automation.
- If administrator elevation is specifically required for a separate command, obtain that through the normal shell flow first; this skill itself does not auto-elevate.

## Notes
- This skill depends on the local `claude` CLI being installed and authenticated.
- This skill is for local Windows automation in this workspace.
- The script is intentionally minimal and deterministic: it wraps `claude -p ...` for reliable OpenClaw use.
