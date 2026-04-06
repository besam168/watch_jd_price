---
name: qq-screenshot
description: Capture a fresh Windows desktop screenshot for QQ replies. Use when the user asks for 截图、截屏、桌面图、当前屏幕、最新桌面. Prefer a Windows GDI live capture by default for truly fresh screenshots, support selecting primary or secondary display, automatically prune old screenshot files, keep PIL/ImageGrab and Win+PrtScn system screenshot paths as fallback/manual options, save into a dedicated QQ output folder, and return MEDIA:<path> for direct reply delivery.
---

# qq-screenshot

Use this skill when the user wants a **fresh Windows desktop screenshot sent back in QQ**.

## What this skill does
- Capture the current desktop screen
- Prefer a **Windows GDI live capture** by default
- Support selecting **primary / secondary / all screens**
- Automatically prune older screenshot files from the QQ output folder
- Keep **PIL / ImageGrab** and **Windows Win + PrtScn** as backup/manual options
- Save each screenshot into a dedicated QQ folder with a new filename
- Return `MEDIA:<path>` for direct OpenClaw media reply

## Default behavior
- Output folder: `C:\Users\besam\.openclaw\workspace\qq-screenshots`
- Capture target: primary screen
- Default method: `gdi` (fresh live capture)
- Output filename: `qq-screenshot_YYYYMMDD_HHMMSS_fff.png`
- Return format: `MEDIA:<absolute-path>`
- Auto-prune: keep the newest 50 screenshot files by default

## Useful options
### Force PIL capture
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method pil
```

### Force Win + PrtScn system screenshot
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method system
```
