---
name: qq-screenshot
description: Capture a fresh Windows desktop screenshot for QQ replies. Use when the user asks for 截图、截屏、桌面图、当前屏幕、最新桌面. Prefer the Windows Win+PrtScn system screenshot path, save into a dedicated QQ output folder, and return MEDIA:<path> for direct reply delivery.
---

# qq-screenshot

Use this skill when the user wants a **fresh Windows desktop screenshot sent back in QQ**.

## What this skill does
- Capture the current primary screen
- Prefer the **Windows Win + PrtScn** system screenshot path by default
- Save each screenshot into a dedicated QQ folder with a new filename
- Return `MEDIA:<path>` for direct OpenClaw media reply

## Best use cases
Use this skill for requests like:
- 截一张桌面图
- 截个屏给我
- 发我当前桌面
- 截图发我
- 再截一张新的
- 用 Win+PrtScn 截图

## Script
- `{baseDir}/scripts/capture-qq.ps1`

## Default behavior
- Output folder: `C:\Users\besam\.openclaw\workspace\qq-screenshots`
- Capture target: primary screen
- Default method: `system` (Win + PrtScn)
- Output filename: `qq-screenshot_YYYYMMDD_HHMMSS_fff.png`
- Return format: `MEDIA:<absolute-path>`

## Recommended command
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1
```

## Useful options
### Force PIL live capture instead of Win + PrtScn
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method pil
```

### Save to a custom folder
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -OutputDir "C:\path\to\folder"
```

### Return plain path instead of MEDIA
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -NoMedia
```

## Notes
- Windows only
- Designed for QQ screenshot replies
- Default to **Win + PrtScn** because the user explicitly prefers that path
- Use `-Method pil` only when the system screenshot path is unsuitable on the current machine
