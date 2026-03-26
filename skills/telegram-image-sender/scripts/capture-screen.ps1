param(
    [string]$OutputPath = "",
    [string]$OutputDir = "",
    [switch]$EmitMedia,
    [switch]$UseVirtualScreen,
    [switch]$UseSystemScreenshot
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

if ($UseSystemScreenshot) {
    $kbSignature = @"
using System;
using System.Runtime.InteropServices;
public static class KeyboardNative {
  [DllImport("user32.dll")]
  public static extern void keybd_event(byte bVk, byte bScan, uint dwFlags, UIntPtr dwExtraInfo);
}
"@
    Add-Type -TypeDefinition $kbSignature

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

    Copy-Item -LiteralPath $latest.FullName -Destination $OutputPath -Force
} else {
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

    $bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

if ($EmitMedia) {
    Write-Output "MEDIA:$OutputPath"
} else {
    Write-Output $OutputPath
}
