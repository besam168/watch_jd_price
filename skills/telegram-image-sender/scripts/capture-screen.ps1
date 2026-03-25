param(
    [string]$OutputPath = "",
    [string]$OutputDir = "",
    [switch]$EmitMedia,
    [switch]$UseVirtualScreen
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

if ($EmitMedia) {
    Write-Output "MEDIA:$OutputPath"
} else {
    Write-Output $OutputPath
}
