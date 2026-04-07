---
name: telegram-live-screenshot
description: Capture a fresh Windows desktop screenshot and return a Telegram-sendable image path from a dedicated output folder. Default to the system screenshot route because it has now been verified to produce real-time images on this machine; keep PIL/ImageGrab as a secondary option and avoid CopyFromScreen as the default because it may freeze on stale frames.
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
- Default method: `system`
- Fallback method: `pil`
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

### Force fallback system screenshot
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1 -Method system
```

### Return plain path instead of MEDIA
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-live.ps1 -NoMedia
```

## Telegram bot direct-send test
Use this when `MEDIA:` path delivery is unreliable and a direct Telegram Bot API send is required.

```powershell
python {baseDir}/scripts/send-telegram-photo.py "C:\path\to\image.png" 8397228579 "最新桌面图"
```

The script:
- reads the Telegram bot token from `C:\Users\besam\.openclaw\openclaw.json`
- sends the image directly with Telegram Bot API `sendPhoto`
- returns JSON with `message_id` when successful

## Notes
- Windows only
- Designed for Telegram screenshot replies
- On this machine, `system` has been verified twice to produce real-time screenshots; use it as the default.
- Keep `pil` as a secondary option when needed for comparison/testing.
- Prefer this skill when older screenshot flows appear stale, cached, or confusing to verify
- Direct-send mode is an external action and should only be used when the user explicitly wants the image sent
