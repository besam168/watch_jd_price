param(
    [string]$OutputPath = "",
    [string]$OutputDir = "",
    [switch]$EmitMedia,
    [switch]$UseVirtualScreen,
    [switch]$UseSystemScreenshot,
    [switch]$OverlayTimestamp,
    [string]$OverlayText = "",
    [ValidateSet('pil','system','copy')]
    [string]$Method = 'pil'
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$skillRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = Join-Path $skillRoot "output"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = Join-Path $OutputDir "telegram-screenshot_$timestamp.png"
} else {
    $resolvedParent = Split-Path -Parent $OutputPath
    if (-not [string]::IsNullOrWhiteSpace($resolvedParent)) {
        New-Item -ItemType Directory -Force -Path $resolvedParent | Out-Null
    }
}

$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

function Invoke-SystemScreenshot {
    param([string]$DestPath)
    $kbSignature = @"
using System;
using System.Runtime.InteropServices;
public static class KeyboardNative {
  [DllImport("user32.dll")]
  public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@
    Add-Type -TypeDefinition $kbSignature -ErrorAction SilentlyContinue

    $VK_SNAPSHOT = 0x2C
    $VK_LWIN = 0x5B
    $KEYEVENTF_KEYUP = 0x0002

    [KeyboardNative]::keybd_event($VK_LWIN, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
    [KeyboardNative]::keybd_event($VK_SNAPSHOT, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 120
    [KeyboardNative]::keybd_event($VK_SNAPSHOT, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 80
    [KeyboardNative]::keybd_event($VK_LWIN, 0, $KEYEVENTF_KEYUP, [UIntPtr]::Zero)
    Start-Sleep -Seconds 2

    $screenshotsDir = Join-Path $env:USERPROFILE "Pictures\Screenshots"
    if (-not (Test-Path $screenshotsDir)) {
        Write-Error "System screenshot folder not found: $screenshotsDir"
        exit 1
    }

    $latest = Get-ChildItem $screenshotsDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $latest) {
        Write-Error "No system screenshots found in: $screenshotsDir"
        exit 1
    }

    Copy-Item -LiteralPath $latest.FullName -Destination $DestPath -Force
}

function Invoke-PilScreenshot {
    param([string]$DestPath, [bool]$DoOverlay, [string]$OverlayString)
    $py = @'
from PIL import ImageGrab, ImageDraw
from pathlib import Path
import sys

out = Path(sys.argv[1])
overlay = sys.argv[2] == "1"
stamp = sys.argv[3]
overlay_text = sys.argv[4] if len(sys.argv) > 4 else ""
img = ImageGrab.grab(all_screens=True)
d = ImageDraw.Draw(img)
if overlay:
    d.rectangle((20,20,520,80), fill=(0,0,0))
    d.text((35,35), stamp, fill=(255,255,255))
if overlay_text:
    d.rectangle((120,120,1200,240), fill=(0,0,0))
    d.text((150,150), overlay_text, fill=(255,64,64))
img.save(out)
print(out)
'@
    $tmp = Join-Path $env:TEMP 'telegram_image_sender_pil.py'
    Set-Content -Path $tmp -Value $py -Encoding UTF8
    $overlayFlag = if ($DoOverlay) { '1' } else { '0' }
    python $tmp $DestPath $overlayFlag $OverlayString $OverlayText | Out-Null
}

function Invoke-CopyScreenshot {
    param([string]$DestPath)
    if ($UseVirtualScreen) {
        $bounds = [System.Windows.Forms.SystemInformation]::VirtualScreen
        $bitmap = New-Object System.Drawing.Bitmap($bounds.Width, $bounds.Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bitmap.Size)
    } else {
        $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
        $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)
    }

    if ($OverlayTimestamp) {
        $font = New-Object System.Drawing.Font("Microsoft YaHei UI", 24, [System.Drawing.FontStyle]::Bold)
        $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255,255,255,255))
        $bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(180,0,0,0))
        $padding = 14
        $textSize = $graphics.MeasureString($stamp, $font)
        $rectWidth = [int][Math]::Ceiling($textSize.Width) + ($padding * 2)
        $rectHeight = [int][Math]::Ceiling($textSize.Height) + ($padding * 2)
        $rectX = 20
        $rectY = 20
        $graphics.FillRectangle($bgBrush, $rectX, $rectY, $rectWidth, $rectHeight)
        $graphics.DrawString($stamp, $font, $textBrush, ($rectX + $padding), ($rectY + $padding))
        $textBrush.Dispose(); $bgBrush.Dispose(); $font.Dispose()
    }

    if (-not [string]::IsNullOrWhiteSpace($OverlayText)) {
        $centerFont = New-Object System.Drawing.Font("Microsoft YaHei UI", 72, [System.Drawing.FontStyle]::Bold)
        $centerBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255,255,64,64))
        $centerBgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(120,0,0,0))
        $padding2 = 24
        $textSize2 = $graphics.MeasureString($OverlayText, $centerFont)
        $rectWidth2 = [int][Math]::Ceiling($textSize2.Width) + ($padding2 * 2)
        $rectHeight2 = [int][Math]::Ceiling($textSize2.Height) + ($padding2 * 2)
        $rectX2 = [int](($bounds.Width - $rectWidth2) / 2)
        $rectY2 = [int](($bounds.Height - $rectHeight2) / 2)
        $graphics.FillRectangle($centerBgBrush, $rectX2, $rectY2, $rectWidth2, $rectHeight2)
        $graphics.DrawString($OverlayText, $centerFont, $centerBrush, ($rectX2 + $padding2), ($rectY2 + $padding2))
        $centerBrush.Dispose(); $centerBgBrush.Dispose(); $centerFont.Dispose()
    }

    $bitmap.Save($DestPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose(); $bitmap.Dispose()
}

if ($UseSystemScreenshot -or $Method -eq 'system') {
    Invoke-SystemScreenshot -DestPath $OutputPath
} elseif ($Method -eq 'copy') {
    Invoke-CopyScreenshot -DestPath $OutputPath
} else {
    Invoke-PilScreenshot -DestPath $OutputPath -DoOverlay:$OverlayTimestamp -OverlayString $stamp
}

if ($EmitMedia) {
    Write-Output "MEDIA:$OutputPath"
} else {
    Write-Output $OutputPath
}
