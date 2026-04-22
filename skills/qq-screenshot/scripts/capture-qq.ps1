param(
    [string]$OutputDir = "C:\Users\besam\.openclaw\workspace\qq-screenshots",
    [switch]$NoMedia,
    [ValidateSet('system','pil','gdi')]
    [string]$Method = 'system',
    [ValidateSet('primary','secondary','all')]
    [string]$Screen = 'primary',
    [int]$KeepCount = 50,
    [switch]$Grid,
    [ValidateSet('quarter','original','two-thirds','one-fifth','double','four-fifths')]
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

function Add-GridOverlay {
    param(
        [string]$ImagePath,
        [string]$Preset
    )

    $presetToCell = @{
        'quarter' = 60
        'original' = 120
        'two-thirds' = 80
        'one-fifth' = 24
        'double' = 48
        'four-fifths' = 19
    }
    $cell = $presetToCell[$Preset]
    if (-not $cell) { $cell = 60 }

    $gridPy = @"
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
import sys

src = Path(sys.argv[1])
preset = sys.argv[2]
cell = int(sys.argv[3])
out = src.with_name(src.stem + '_grid_' + preset + src.suffix)

img = Image.open(src).convert('RGB')
draw = ImageDraw.Draw(img)
w, h = img.size
cols = math.ceil(w / cell)
rows = math.ceil(h / cell)
letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

font_size = 16
if cell <= 80:
    font_size = 12
if cell <= 60:
    font_size = 10
if cell <= 24:
    font_size = 8
if cell <= 19:
    font_size = 7

try:
    font = ImageFont.truetype('arial.ttf', font_size)
except Exception:
    font = ImageFont.load_default()

line_w = 2 if cell >= 60 else 1
for c in range(1, cols):
    x = c * cell
    draw.line((x, 0, x, h), fill=(255, 0, 0), width=line_w)
for r in range(1, rows):
    y = r * cell
    draw.line((0, y, w, y), fill=(255, 0, 0), width=line_w)
for r in range(rows):
    for c in range(cols):
        row_label = letters[r] if r < len(letters) else f'R{r+1}'
        label = f'{row_label}{c+1}'
        x0 = c * cell
        y0 = r * cell
        rect_w = max(14, min(cell - 2, int(cell * 0.75)))
        rect_h = max(8, min(cell - 2, int(cell * 0.28)))
        draw.rectangle((x0 + 1, y0 + 1, x0 + rect_w, y0 + rect_h), fill=(255,255,255))
        draw.text((x0 + 2, y0 + 1), label, fill=(255,0,0), font=font)

img.save(out)
print(str(out))
"@

    $tmpDir = Join-Path $OutputDir '.tmp'
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null
    $tmpPy = Join-Path $tmpDir ("qq-grid-" + [guid]::NewGuid().ToString() + ".py")
    Set-Content -LiteralPath $tmpPy -Value $gridPy -Encoding UTF8
    try {
        $gridPath = python $tmpPy $ImagePath $Preset $cell
        return ($gridPath | Select-Object -Last 1).Trim()
    } finally {
        Remove-Item -LiteralPath $tmpPy -Force -ErrorAction SilentlyContinue
    }
}

if ($Grid) {
    $gridOutput = Add-GridOverlay -ImagePath $outputPath -Preset $GridPreset
    if (-not (Test-Path $gridOutput)) {
        throw "Grid screenshot file was not created: $gridOutput"
    }
    $outputPath = $gridOutput
}

if (-not (Test-Path $outputPath)) {
    throw "Screenshot file was not created: $outputPath"
}

if ($KeepCount -gt 0) {
    $allShots = Get-ChildItem -Path $OutputDir -File -Filter "qq-screenshot_*.png" | Sort-Object LastWriteTime -Descending
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
