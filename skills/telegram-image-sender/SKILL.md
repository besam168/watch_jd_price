---
name: telegram-image-sender
description: Capture Windows desktop screenshots and return a Telegram-sendable image path. Use when the user asks to screenshot the current screen, send the current desktop in Telegram, or save a screenshot PNG for follow-up sharing.
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

## What this skill is good for
- Capture the current primary screen as PNG
- Optionally capture the full virtual desktop across monitors
- Save screenshots into a predictable output directory
- Return either:
  - a plain file path, or
  - `MEDIA:<path>` for direct OpenClaw media delivery

## Files
- Script: `{baseDir}/scripts/capture-screen.ps1`
- Default output directory: `{baseDir}/output/`

## Default workflow

### 1) Capture and directly prepare a Telegram-sendable result

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -EmitMedia
```

This prints:

```text
MEDIA:C:\path\to\telegram-screenshot_20260325_202500.png
```

Use that line directly in the assistant reply when the runtime supports outbound media.

### 2) Capture and return only the PNG path

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1
```

### 3) Capture to a custom path

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -OutputPath "C:\path\to\shot.png"
```

### 4) Capture all monitors as one virtual desktop image

```powershell
powershell -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-screen.ps1 -EmitMedia -UseVirtualScreen
```

## Output conventions
- Default filename pattern:
  - `telegram-screenshot_YYYYMMDD_HHMMSS.png`
- Default directory:
  - `{baseDir}/output/`
- `-EmitMedia` output format:
  - `MEDIA:<absolute-path>`

## Recommended response behavior
- If the user asked to **see the screenshot in Telegram now**, run with `-EmitMedia` and send the returned `MEDIA:` line.
- If the user asked to **save** a screenshot, return the file path.
- If direct media sending is unavailable in the current runtime, keep the PNG and offer fallback delivery.

## Notes
- Windows only
- Uses PowerShell plus `System.Windows.Forms` and `System.Drawing`
- The direct Telegram path has been verified in this workspace via OpenClaw `MEDIA:<path>` replies
