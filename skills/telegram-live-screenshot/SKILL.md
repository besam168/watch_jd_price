---
name: telegram-live-screenshot
description: Capture a fresh Windows desktop screenshot and return a Telegram-sendable image path from a dedicated output folder. Use when the user wants a current/live screenshot, asks to send the desktop to Telegram, or when the older screenshot route appears cached or unreliable.
---

# telegram-live-screenshot

Use this skill when the user wants a **fresh/live Windows desktop screenshot** sent back into Telegram.

## What this skill does
- Capture the current primary screen
- Save each screenshot into a dedicated folder with a new filename
- Optionally overlay the current timestamp on the image
- Return `MEDIA:<path>` so the image can be sent back to Telegram

## Best use cases
Use this skill for requests like:
- 截一张最新桌面图
- 发我当前桌面
- 截个实时屏幕给我
- 再截一张新的
- 旧截图不对，重新现截

## Script
- `{baseDir}/scripts/capture-live.ps1`

## Default behavior
- Output folder: `C:\Users\besam\.openclaw\workspace\new photo`
- Capture target: primary screen
- Output filename: `live-screenshot_YYYYMMDD_HHMMSS_fff.png`
- Return format: `MEDIA:<absolute-path>`

## Recommended command
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1
```

## Useful options
### Save to a custom folder
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1 -OutputDir "C:\path\to\folder"
```

### Add a visible timestamp overlay
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1 -OverlayTimestamp
```

### Return plain path instead of MEDIA
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1 -NoMedia
```

## Notes
- Windows only
- Designed for Telegram screenshot replies
- Prefer this skill when older screenshot flows appear stale, cached, or confusing to verify
