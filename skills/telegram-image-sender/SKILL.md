---
name: telegram-image-sender
description: Capture desktop screenshots on Windows and prepare images for sending in chat or email. Use when the user asks to screenshot the current screen, save a screenshot file, or prepare an image to send through Telegram-compatible workflows.
---

# telegram-image-sender

A minimal local skill for screenshot-first image delivery.

## When to use
Use this skill when the user asks for any of the following:
- "截个图给我"
- "把当前屏幕发我"
- "截图发邮箱"
- "准备一张图片给 Telegram/聊天里发送"

## What this skill does now
Current reliable capability:
1. Capture the current Windows desktop to a PNG file
2. Save the image into the workspace
3. Return the saved path for follow-up delivery
4. Optional fallback: attach the PNG to an email using an existing mail script

## Current limitation
This local version does **not** yet have a dedicated native Telegram media-upload tool.
So the safe workflow is:
1. Capture screenshot
2. If native media sending is available in the current runtime, send it
3. Otherwise send by email or keep the PNG locally

## Workflow

### Capture current screen
Run:

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1
```

Optional custom output path:

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -OutputPath "C:\path\to\shot.png"
```

### Result handling
- On success, the script prints the full PNG path
- Use that path for follow-up actions
- Preferred default filename pattern:
  - `screenshot_YYYYMMDD_HHMMSS.png`

## Notes
- Windows only
- Captures the full primary desktop surface
- If the user asks to send the screenshot in chat and no native image-send route exists, tell them clearly and offer email fallback
