param(
    [string]$OutputDir = "C:\Users\besam\.openclaw\workspace\new photo",
    [switch]$OverlayTimestamp,
    [switch]$NoMedia
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
$outputPath = Join-Path $OutputDir "live-screenshot_$timestamp.png"

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.Location, [System.Drawing.Point]::Empty, $bounds.Size)

if ($OverlayTimestamp) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss.fff"
    $font = New-Object System.Drawing.Font("Microsoft YaHei UI", 24, [System.Drawing.FontStyle]::Bold)
    $textBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White)
    $bgBrush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(180,0,0,0))
    $padding = 14
    $textSize = $graphics.MeasureString($stamp, $font)
    $rectWidth = [int][Math]::Ceiling($textSize.Width) + ($padding * 2)
    $rectHeight = [int][Math]::Ceiling($textSize.Height) + ($padding * 2)
    $rectX = 20
    $rectY = 20
    $graphics.FillRectangle($bgBrush, $rectX, $rectY, $rectWidth, $rectHeight)
    $graphics.DrawString($stamp, $font, $textBrush, ($rectX + $padding), ($rectY + $padding))
    $textBrush.Dispose()
    $bgBrush.Dispose()
    $font.Dispose()
}

$bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

if ($NoMedia) {
    Write-Output $outputPath
} else {
    Write-Output "MEDIA:$outputPath"
}
