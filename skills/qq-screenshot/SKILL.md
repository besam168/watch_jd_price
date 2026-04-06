---
name: qq-screenshot
description: Capture a fresh Windows desktop screenshot for QQ replies. Use when the user asks for 截图、截屏、桌面图、当前屏幕、最新桌面. Prefer a live PIL/ImageGrab capture by default for truly fresh screenshots, support selecting primary or secondary display, automatically prune old screenshot files, keep the Windows Win+PrtScn system screenshot path as a fallback/manual option, save into a dedicated QQ output folder, and return MEDIA:<path> for direct reply delivery.
---

# qq-screenshot

Use this skill when the user wants a **fresh Windows desktop screenshot sent back in QQ**.

## What this skill does
- Capture the current desktop screen
- Prefer a **live PIL / ImageGrab** capture by default
- Support selecting **primary / secondary / all screens**
- Automatically prune older screenshot files from the QQ output folder
- Keep the **Windows Win + PrtScn** system screenshot path as a backup/manual option
- Save each screenshot into a dedicated QQ folder with a new filename
- Return `MEDIA:<path>` for direct OpenClaw media reply

## Best use cases
Use this skill for requests like:
- 截一张桌面图
- 截个屏给我
- 发我当前桌面
- 截图发我
- 再截一张新的
- 截主屏
- 截副屏
- 用 Win+PrtScn 截图

## Script
- `{baseDir}/scripts/capture-qq.ps1`

## Default behavior
- Output folder: `C:\Users\besam\.openclaw\workspace\qq-screenshots`
- Capture target: primary screen
- Default method: `pil` (fresh live capture)
- Output filename: `qq-screenshot_YYYYMMDD_HHMMSS_fff.png`
- Return format: `MEDIA:<absolute-path>`
- Auto-prune: keep the newest 50 screenshot files by default

## Recommended command
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1
```

## Useful options
### Force Win + PrtScn system screenshot
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method system
```

### Capture all displays in one image
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Screen all
```

### Capture the secondary display
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Screen secondary
```

### Keep more history files
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -KeepCount 100
```

### Return plain path instead of MEDIA
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -NoMedia
```

## Notes
- Windows only
- Designed for QQ screenshot replies
- Default to **PIL / ImageGrab** because this machine needs truly fresh screenshots
- Keep `-Method system` only as a backup/manual path when explicitly needed
