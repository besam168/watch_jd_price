param(
    [string]$OutputPath = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Get-ScreenshotPath([string]$requestedPath) {
    if (-not [string]::IsNullOrWhiteSpace($requestedPath)) {
        return $requestedPath
    }

    $tempDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'temp'
    if (!(Test-Path $tempDir)) {
        New-Item -ItemType Directory -Force -Path $tempDir | Out-Null
    }
    return (Join-Path $tempDir ("screen-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".png"))
}

$targetPath = Get-ScreenshotPath $OutputPath
$targetDir = Split-Path $targetPath -Parent
if ($targetDir -and !(Test-Path $targetDir)) {
    New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
}

$bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bitmap.Size)
$bitmap.Save($targetPath, [System.Drawing.Imaging.ImageFormat]::Png)
$graphics.Dispose()
$bitmap.Dispose()

Write-Output $targetPath
