param(
    [string]$OutputDir = "C:\Users\besam\.openclaw\workspace\new photo",
    [switch]$OverlayTimestamp,
    [switch]$NoMedia,
    [ValidateSet('pil','system')]
    [string]$Method = 'system'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputPath = Join-Path $OutputDir "live-screenshot_$timestamp.png"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"

if ($Method -eq 'system') {
    $captureScript = "C:\Users\besam\.openclaw\workspace\skills\telegram-image-sender\scripts\capture-screen.ps1"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $captureScript -UseSystemScreenshot -OutputPath $outputPath | Out-Null
} else {
    $py = @'
from PIL import ImageGrab, ImageDraw
from datetime import datetime
from pathlib import Path
import sys

out = Path(sys.argv[1])
overlay = sys.argv[2] == "1"
stamp = sys.argv[3]
img = ImageGrab.grab(all_screens=False)
if overlay:
    d = ImageDraw.Draw(img)
    d.rectangle((20,20,520,80), fill=(0,0,0))
    d.text((35,35), stamp, fill=(255,255,255))
img.save(out)
print(out)
'@
    $tmp = Join-Path $env:TEMP 'telegram_live_capture_pil.py'
    Set-Content -Path $tmp -Value $py -Encoding UTF8
    $overlayFlag = if ($OverlayTimestamp) { '1' } else { '0' }
    python $tmp $outputPath $overlayFlag $stamp | Out-Null
}

if ($NoMedia) {
    Write-Output $outputPath
} else {
    Write-Output "MEDIA:$outputPath"
}
