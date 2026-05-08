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
- Support a **standard grid screenshot** mode for click guidance
- Save each screenshot into a dedicated QQ folder with a new filename
- Return `MEDIA:<path>` for direct OpenClaw media reply

## Default behavior
- Output folder: `C:\Users\besam\.openclaw\workspace\qq-screenshots`
- Capture target: primary screen
- Default method: `system` (latest verified realtime path on this machine)
- Output filename: `qq-screenshot_YYYYMMDD_HHMMSS_fff.png`
- Grid screenshot filename: `qq-grid_YYYYMMDD_HHMMSS_fff.png`
- Return format: `MEDIA:<absolute-path>`
- Auto-prune: keep the newest 50 screenshot files by default
- Standard grid preset: `quarter`

## Useful options
### Force PIL capture
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method pil
```

### Force Win + PrtScn system screenshot
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method system
```

### Standard grid screenshot
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File {baseDir}/scripts/capture-qq.ps1 -Method system -Grid -GridPreset quarter
```

## Long-term standard
- 用户说：`截图` → 返回普通截图
- 用户说：`网格截图` → 返回**标准网格截图**
- 当前标准网格截图固定为：
  - `quarter` 预设
  - **正方小格**
  - **每个格子单独编号**
  - **按行编号**：第一行 `A1 A2 A3 ...`，第二行 `B1 B2 B3 ...`，后面依次往下推
  - 当前实现基线：约 `40px` 一格、红线、白底红字小标签
- 这是 QQ 点击辅助场景的默认长期规格，后续不要再临时改回别的编号方式

