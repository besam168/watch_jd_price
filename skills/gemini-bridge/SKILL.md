---
name: gemini-bridge
description: Use Google's Gemini API from OpenClaw on this Windows machine. Trigger when the user wants Gemini to analyze, draft, summarize, review code, or generate files/content locally through Gemini API calls, including OpenAI-compatible mode when a tool expects OpenAI format.
---

# gemini-bridge

Use this skill when the user explicitly wants **Gemini** to do work through a local bridge script instead of relying on a GUI plugin.

## What this skill does
- Calls Gemini through the Google Generative Language API
- Supports the standard Gemini endpoint
- Supports the OpenAI-compatible endpoint when needed
- Returns plain text or JSON
- Can save Gemini output directly to a file
- Provides a task wrapper for common reusable workflows
- Exposes a simple VS Code Tasks entry point for local usage

## Scripts
- `{baseDir}/scripts/run-gemini.ps1`
- `{baseDir}/scripts/run-gemini-task.ps1`

## Required config
The script expects either:
- `-ApiKey`, or
- `GOOGLE_API_KEY` in the environment

Default model:
- `gemini-2.5-flash`

Default standard base URL:
- `https://generativelanguage.googleapis.com/v1beta`

OpenAI-compatible base URL when needed:
- `https://generativelanguage.googleapis.com/v1beta`
- Or `https://generativelanguage.googleapis.com/v1beta/openai`

## `run-gemini.ps1`

### Main parameters
- `Prompt`
- `ApiKey`
- `Model`
- `BaseUrl`
- `OutputFile`
- `Json`
- `OpenAICompat`
- `MaxRetries`
- `RetryDelaySeconds`

### Built-in reliability
- Normalizes raw model names like `gemini-2.5-flash`
- Also accepts native names like `models/gemini-2.5-flash`
- Avoids double-appending `/openai` in OpenAI-compatible mode
- Retries transient failures for `408`, `429`, `500`, `502`, `503`, `504`
- Returns structured JSON errors when `-Json` is enabled

### Error categories
- `bad_request`
- `unauthorized`
- `forbidden`
- `not_found`
- `timeout`
- `rate_limited`
- `server_error`
- `service_unavailable`
- `gateway_timeout`
- `http_error`

## Primary workflows

### 1) Standard Gemini call
```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini.ps1 -Prompt "Summarize this project in 5 bullets."
```

### 2) Save Gemini output to a file
```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini.ps1 -Prompt "Draft a SKILL.md for a weather skill." -OutputFile "C:\path\to\draft.md"
```

### 3) JSON output
```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini.ps1 -Prompt "Reply with exactly GEMINI_OK" -Json
```

### 4) OpenAI-compatible mode
```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini.ps1 -Prompt "Reply with exactly GEMINI_OK" -BaseUrl "https://generativelanguage.googleapis.com/v1beta/openai" -OpenAICompat
```

## `run-gemini-task.ps1`

### Supported tasks
- `repo-analyze`
- `file-draft`
- `summarize-text`
- `code-review`

### Example task calls
```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini-task.ps1 -Task repo-analyze -Workdir "C:\path\to\project" -Json
```

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/run-gemini-task.ps1 -Task code-review -TargetPath "C:\path\to\file.ps1" -Json
```

## VS Code usage
This skill is also wired into:
- `{workspace}/.vscode/tasks.json`

Available task labels:
- `Gemini Bridge: Quick Test`
- `Gemini Bridge: Repo Analyze`
- `Gemini Bridge: Summarize Selection`

Run them in VS Code through:
- `Terminal -> Run Task`

## Verified status
Confirmed working in this workspace:
- Native Gemini call with model `gemini-2.5-flash`
- Successful test response: `GEMINI_25_FLASH_OK`
- Task wrapper execution succeeded for `repo-analyze`

Known limitation:
- `gemini-3.1-pro-preview` currently returned `429 Too Many Requests` during testing, which looks like a model-specific limit/rate issue rather than a bridge failure.

## Recommended usage rules
- Prefer the standard Gemini endpoint unless a specific tool/plugin expects OpenAI format.
- Prefer `gemini-2.5-flash` as the default stable model in this environment.
- Use `-Json` for automation and downstream parsing.
- Use `-OutputFile` when Gemini should draft a file directly.
- Treat HTTP `429` as a quota/rate-limit signal, not necessarily a bad API key.

## Notes
- This is a local API bridge skill, not a GUI integration.
- It is intended to be the foundation for higher-level workflows, including Claude-to-Gemini delegation later.
