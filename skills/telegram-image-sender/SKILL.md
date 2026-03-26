---
name: telegram-image-sender
description: Capture Windows desktop screenshots and return a Telegram-sendable image path. Supports direct PowerShell capture and system-level realtime screenshots via Win+PrtScn.
---

# telegram-image-sender

Use this skill for Windows desktop screenshots that should be sent back into Telegram or saved as PNG files.

## Triggers
Use when the user says things like:
- 截个图给我
- 把当前屏幕发我
- 发我电脑屏幕
- 截图发 Telegram
- 保存一张屏幕截图
- 实时截一下桌面

## What this skill is good for
- Capture the current primary screen as PNG
- Optionally capture the full virtual desktop across monitors
- Capture a system-level realtime screenshot using `Win + PrtScn`
- Save screenshots into a predictable output directory
- Return either:
  - a plain file path, or
  - `MEDIA:<path>` for direct OpenClaw media delivery

## Files
- Script: `{baseDir}/scripts/capture-screen.ps1`
- Default output directory: `{baseDir}/output/`

## Default workflows

### 1) Direct PowerShell capture and immediate Telegram send

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -EmitMedia
```

### 2) Full virtual desktop capture

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -EmitMedia -UseVirtualScreen
```

### 3) System realtime screenshot via Win + PrtScn

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -EmitMedia -UseSystemScreenshot
```

This mode:
- sends the Windows system screenshot hotkey
- reads the latest file from `Pictures\Screenshots`
- copies it into the skill output folder
- returns `MEDIA:<absolute-path>`

## Output conventions
- Default filename pattern:
  - `telegram-screenshot_YYYYMMDD_HHMMSS.png`
- Default directory:
  - `{baseDir}/output/`
- `-EmitMedia` output format:
  - `MEDIA:<absolute-path>`

## Recommended response behavior
- If the user wants a quick local screenshot, use the default direct capture path.
- If the user specifically wants a **realtime desktop screenshot**, prefer `-UseSystemScreenshot`.
- If the user wants all monitors, use `-UseVirtualScreen`.

## Notes
- Windows only
- Direct capture uses `System.Windows.Forms` + `System.Drawing`
- System realtime mode uses the Windows `Win + PrtScn` screenshot flow
- The Telegram return path has been validated in this workspace
