param(
    [string]$OutputDir = "C:\Users\besam\.openclaw\workspace\qq-screenshots",
    [switch]$NoMedia,
    [ValidateSet('system','pil','gdi')]
    [string]$Method = 'system',
    [ValidateSet('primary','secondary','all')]
    [string]$Screen = 'primary',
    [int]$KeepCount = 50,
    [switch]$Grid,
    [ValidateSet('quarter','six')]
    [string]$GridPreset = 'quarter'
)

$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputPath = Join-Path $OutputDir "qq-screenshot_$timestamp.png"

$telegramCaptureScript = "C:\Users\besam\.openclaw\workspace\skills\telegram-image-sender\scripts\capture-screen.ps1"
$pythonScript = @"
from PIL import ImageGrab
import sys
import ctypes


def choose_bbox(all_screens=False, screen='primary'):
    if all_screens:
        return None
    try:
        user32 = ctypes.windll.user32
        screens = user32.GetSystemMetrics(80)
        if screens <= 1:
            return None
        virtual_left = user32.GetSystemMetrics(76)
        virtual_width = user32.GetSystemMetrics(78)
        primary_width = user32.GetSystemMetrics(0)
        primary_height = user32.GetSystemMetrics(1)
        if screen == 'primary':
            return (0, 0, primary_width, primary_height)
        if screen == 'secondary':
            if virtual_left < 0:
                return (virtual_left, 0, 0, primary_height)
            if virtual_width > primary_width:
                return (primary_width, 0, virtual_left + virtual_width, primary_height)
            return None
    except Exception:
        return None
    return None

output = sys.argv[1]
screen = sys.argv[2]
all_screens = screen == 'all'
bbox = choose_bbox(all_screens=all_screens, screen=screen)
img = ImageGrab.grab(all_screens=all_screens, bbox=bbox)
img.save(output)
print(output)
"@

function Invoke-PilCapture {
    $tempDir = Join-Path $OutputDir ".tmp"
    New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    $tempPy = Join-Path $tempDir ("qq-screenshot-capture-" + [guid]::NewGuid().ToString() + ".py")
    Set-Content -LiteralPath $tempPy -Value $pythonScript -Encoding UTF8
    try {
        python $tempPy $outputPath $Screen | Out-Null
    } finally {
        Remove-Item -LiteralPath $tempPy -Force -ErrorAction SilentlyContinue
    }
}

function Invoke-GdiCapture {
    Add-Type -AssemblyName System.Drawing
    Add-Type -AssemblyName System.Windows.Forms

    function Get-VirtualBounds {
        return [System.Windows.Forms.SystemInformation]::VirtualScreen
    }

    function Get-PrimaryBounds {
        return [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    }

    function Get-SecondaryBounds {
        $screens = [System.Windows.Forms.Screen]::AllScreens
        foreach ($s in $screens) {
            if (-not $s.Primary) { return $s.Bounds }
        }
        return [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    }

    switch ($Screen) {
        'all' { $bounds = Get-VirtualBounds }
        'secondary' { $bounds = Get-SecondaryBounds }
        default { $bounds = Get-PrimaryBounds }
    }

    $bmp = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bmp)
    try {
        $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bounds.Size)
        $bmp.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
    } finally {
        $graphics.Dispose()
        $bmp.Dispose()
    }
}

function Invoke-SystemCapture {
    $screenshotsDir = Join-Path $env:USERPROFILE "Pictures\Screenshots"
    $baselineTicks = 0
    if (Test-Path $screenshotsDir) {
        $before = Get-ChildItem $screenshotsDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($before) {
            $baselineTicks = $before.LastWriteTimeUtc.Ticks
        }
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $telegramCaptureScript -UseSystemScreenshot -OutputPath $outputPath | Out-Null

    $copiedOk = $false
    if (Test-Path $outputPath) {
        try {
            $copiedItem = Get-Item $outputPath
            if ($copiedItem.Length -gt 0) {
                if (-not (Test-Path $screenshotsDir)) {
                    $copiedOk = $true
                } else {
                    $after = Get-ChildItem $screenshotsDir -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
                    if ($after -and $after.LastWriteTimeUtc.Ticks -gt $baselineTicks) {
                        $copiedOk = $true
                    }
                }
            }
        } catch {
            $copiedOk = $false
        }
    }

    if (-not $copiedOk) {
        if (Test-Path $outputPath) {
            Remove-Item -LiteralPath $outputPath -Force -ErrorAction SilentlyContinue
        }
        Invoke-GdiCapture
    }
}

switch ($Method) {
    'system' { Invoke-SystemCapture }
    'pil' { Invoke-PilCapture }
    default { Invoke-GdiCapture }
}

if (-not (Test-Path $outputPath)) {
    throw "Screenshot file was not created: $outputPath"
}

if ($Grid) {
    $gridScript = "C:\Users\besam\.openclaw\workspace\skills\qq-screenshot\scripts\make-grid.py"
    $gridPath = Join-Path $OutputDir ("qq-grid_" + $timestamp + ".png")
    python $gridScript --input $outputPath --output $gridPath --preset $GridPreset | Out-Null
    if (-not (Test-Path $gridPath)) {
        throw "Grid screenshot file was not created: $gridPath"
    }
    $outputPath = $gridPath
}

if ($KeepCount -gt 0) {
    $allShots = Get-ChildItem -Path $OutputDir -File | Where-Object { $_.Name -like 'qq-screenshot_*.png' -or $_.Name -like 'qq-grid_*.png' } | Sort-Object LastWriteTime -Descending
    if ($allShots.Count -gt $KeepCount) {
        $toRemove = $allShots | Select-Object -Skip $KeepCount
        foreach ($item in $toRemove) {
            Remove-Item -LiteralPath $item.FullName -Force -ErrorAction SilentlyContinue
        }
    }
}

if ($NoMedia) {
    Write-Output $outputPath
} else {
    Write-Output "MEDIA:$outputPath"
}
