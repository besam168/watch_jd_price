param(
    [string]$OutputPath = "",
    [switch]$VirtualScreen,
    [Nullable[int]]$X = $null,
    [Nullable[int]]$Y = $null,
    [Nullable[int]]$Width = $null,
    [Nullable[int]]$Height = $null
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $scriptRoot "capture-style-test.png"
} else {
    $resolvedParent = Split-Path -Parent $OutputPath
    if (-not [string]::IsNullOrWhiteSpace($resolvedParent)) {
        New-Item -ItemType Directory -Force -Path $resolvedParent | Out-Null
    }
}

$bounds = if ($VirtualScreen) {
    [System.Windows.Forms.SystemInformation]::VirtualScreen
} else {
    [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
}

$hasRegion = $X -ne $null -or $Y -ne $null -or $Width -ne $null -or $Height -ne $null
if ($hasRegion) {
    $captureX = if ($X -ne $null) { [int]$X } else { $bounds.X }
    $captureY = if ($Y -ne $null) { [int]$Y } else { $bounds.Y }
    $captureWidth = if ($Width -ne $null) { [int]$Width } else { $bounds.Width }
    $captureHeight = if ($Height -ne $null) { [int]$Height } else { $bounds.Height }

    if ($captureWidth -le 0 -or $captureHeight -le 0) {
        throw "Width and height must be positive when region capture is used."
    }

    $minX = $bounds.X
    $minY = $bounds.Y
    $maxX = $bounds.X + $bounds.Width
    $maxY = $bounds.Y + $bounds.Height

    if ($captureX -lt $minX) { $captureX = $minX }
    if ($captureY -lt $minY) { $captureY = $minY }
    if ($captureX + $captureWidth -gt $maxX) { $captureWidth = $maxX - $captureX }
    if ($captureY + $captureHeight -gt $maxY) { $captureHeight = $maxY - $captureY }

    if ($captureWidth -le 0 -or $captureHeight -le 0) {
        throw "Requested region falls outside the capturable screen bounds."
    }

    $captureBounds = New-Object System.Drawing.Rectangle($captureX, $captureY, $captureWidth, $captureHeight)
} else {
    $captureBounds = New-Object System.Drawing.Rectangle($bounds.X, $bounds.Y, $bounds.Width, $bounds.Height)
}

$bitmap = New-Object System.Drawing.Bitmap $captureBounds.Width, $captureBounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($captureBounds.X, $captureBounds.Y, 0, 0, $captureBounds.Size)
$bitmap.Save($OutputPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Output $OutputPath
