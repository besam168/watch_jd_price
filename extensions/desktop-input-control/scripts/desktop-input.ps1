param(
    [Parameter(Mandatory=$true)]
    [string]$Action,
    [string]$Arg1 = "",
    [string]$Arg2 = "",
    [string]$Arg3 = "",
    [string]$Arg4 = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
Add-Type -AssemblyName Microsoft.VisualBasic

$signature = @"
using System;
using System.Runtime.InteropServices;
public static class DesktopInputNative {
  [StructLayout(LayoutKind.Sequential)]
  public struct POINT {
    public int X;
    public int Y;
  }

  [DllImport("user32.dll")]
  public static extern bool SetCursorPos(int X, int Y);

  [DllImport("user32.dll")]
  public static extern bool GetCursorPos(out POINT lpPoint);

  [DllImport("user32.dll")]
  public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}
"@
Add-Type -TypeDefinition $signature

$MOUSEEVENTF_LEFTDOWN = 0x0002
$MOUSEEVENTF_LEFTUP = 0x0004
$MOUSEEVENTF_RIGHTDOWN = 0x0008
$MOUSEEVENTF_RIGHTUP = 0x0010
$MOUSEEVENTF_WHEEL = 0x0800

function Invoke-LeftDown {
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
}

function Invoke-LeftUp {
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
}

function Invoke-LeftClick {
    Invoke-LeftDown
    Start-Sleep -Milliseconds 40
    Invoke-LeftUp
}

function Invoke-RightClick {
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 40
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_RIGHTUP, 0, 0, 0, [UIntPtr]::Zero)
}

function Get-CursorPosition {
    $point = New-Object DesktopInputNative+POINT
    [DesktopInputNative]::GetCursorPos([ref]$point) | Out-Null
    return $point
}

function Convert-ToSendKeysTarget([string]$value, $map) {
    if ($map.ContainsKey($value)) { return $map[$value] }
    return $value
}

function Find-WindowTarget([string]$query) {
    $q = $query.Trim().ToLowerInvariant()
    if ([string]::IsNullOrWhiteSpace($q)) { return $null }

    $procs = Get-Process | Where-Object {
        $_.MainWindowHandle -ne 0 -and (
            ($_.MainWindowTitle -and $_.MainWindowTitle.ToLowerInvariant().Contains($q)) -or
            $_.ProcessName.ToLowerInvariant().Contains($q)
        )
    } | Sort-Object StartTime

    if ($procs -and $procs.Count -gt 0) {
        return $procs[-1]
    }
    return $null
}

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

function Save-ScreenCapture([string]$targetPath) {
    $bounds = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
    $bitmap = New-Object System.Drawing.Bitmap $bounds.Width, $bounds.Height
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.CopyFromScreen($bounds.X, $bounds.Y, 0, 0, $bitmap.Size)
    $bitmap.Save($targetPath, [System.Drawing.Imaging.ImageFormat]::Png)
    $graphics.Dispose()
    $bitmap.Dispose()
}

switch ($Action) {
    "mouse-move" {
        $x = [int][math]::Round([double]$Arg1)
        $y = [int][math]::Round([double]$Arg2)
        [DesktopInputNative]::SetCursorPos($x, $y) | Out-Null
        Write-Output "Mouse moved to ($x, $y)"
    }
    "mouse-move-relative" {
        $dx = [int][math]::Round([double]$Arg1)
        $dy = [int][math]::Round([double]$Arg2)
        $point = Get-CursorPosition
        $x = $point.X + $dx
        $y = $point.Y + $dy
        [DesktopInputNative]::SetCursorPos($x, $y) | Out-Null
        Write-Output "Mouse moved relatively by ($dx, $dy) to ($x, $y)"
    }
    "mouse-click" {
        $button = ($Arg1 | ForEach-Object { $_.ToLowerInvariant() })
        if ($button -eq "right") {
            Invoke-RightClick
            Write-Output "Mouse right click sent"
        } elseif ($button -eq "middle") {
            [DesktopInputNative]::mouse_event(0x0020, 0, 0, 0, [UIntPtr]::Zero)
            Start-Sleep -Milliseconds 40
            [DesktopInputNative]::mouse_event(0x0040, 0, 0, 0, [UIntPtr]::Zero)
            Write-Output "Mouse middle click sent"
        } elseif ($button -eq "double") {
            Invoke-LeftClick
            Start-Sleep -Milliseconds 80
            Invoke-LeftClick
            Write-Output "Mouse double click sent"
        } else {
            Invoke-LeftClick
            Write-Output "Mouse left click sent"
        }
    }
    "mouse-drag" {
        $x1 = [int][math]::Round([double]$Arg1)
        $y1 = [int][math]::Round([double]$Arg2)
        $x2 = [int][math]::Round([double]$Arg3)
        $y2 = [int][math]::Round([double]$Arg4)
        [DesktopInputNative]::SetCursorPos($x1, $y1) | Out-Null
        Start-Sleep -Milliseconds 60
        Invoke-LeftDown
        Start-Sleep -Milliseconds 80
        [DesktopInputNative]::SetCursorPos($x2, $y2) | Out-Null
        Start-Sleep -Milliseconds 80
        Invoke-LeftUp
        Write-Output "Mouse dragged from ($x1, $y1) to ($x2, $y2)"
    }
    "mouse-scroll" {
        $delta = if ($Arg1 -eq "down") { -240 } elseif ($Arg1 -eq "up") { 240 } else { [int][math]::Round([double]$Arg1) }
        $wheelData = [BitConverter]::ToUInt32([BitConverter]::GetBytes([int]$delta), 0)
        [DesktopInputNative]::mouse_event($MOUSEEVENTF_WHEEL, 0, 0, $wheelData, [UIntPtr]::Zero)
        Write-Output "Mouse wheel scrolled by $delta"
    }
    "type-text" {
        [System.Windows.Forms.SendKeys]::SendWait($Arg1)
        Write-Output "Typed text: $Arg1"
    }
    "press-hotkey" {
        $raw = $Arg1.Trim().ToLowerInvariant()
        $map = @{
            "ctrl" = "^"
            "alt" = "%"
            "shift" = "+"
            "win" = "^(%{ESC})"
            "enter" = "{ENTER}"
            "tab" = "{TAB}"
            "esc" = "{ESC}"
            "delete" = "{DELETE}"
            "backspace" = "{BACKSPACE}"
            "space" = " "
            "up" = "{UP}"
            "down" = "{DOWN}"
            "left" = "{LEFT}"
            "right" = "{RIGHT}"
            "f1" = "{F1}"
            "f2" = "{F2}"
            "f3" = "{F3}"
            "f4" = "{F4}"
            "f5" = "{F5}"
            "f6" = "{F6}"
            "f7" = "{F7}"
            "f8" = "{F8}"
            "f9" = "{F9}"
            "f10" = "{F10}"
            "f11" = "{F11}"
            "f12" = "{F12}"
        }

        if ($raw -eq "win+r") {
            [System.Windows.Forms.SendKeys]::SendWait("^(%{ESC})")
            Start-Sleep -Milliseconds 250
            [System.Windows.Forms.SendKeys]::SendWait("r")
            Write-Output "Pressed hotkey: win+r"
            break
        }

        $parts = $raw -split "\+"
        if ($parts.Count -eq 1) {
            $single = $parts[0]
            [System.Windows.Forms.SendKeys]::SendWait((Convert-ToSendKeysTarget $single $map))
            Write-Output "Pressed hotkey: $raw"
            break
        }

        $modPrefix = ""
        $last = $parts[$parts.Count - 1]
        for ($i = 0; $i -lt $parts.Count - 1; $i++) {
            $p = $parts[$i]
            if ($map.ContainsKey($p) -and ($p -eq "ctrl" -or $p -eq "alt" -or $p -eq "shift")) {
                $modPrefix += $map[$p]
            }
        }

        $target = Convert-ToSendKeysTarget $last $map
        [System.Windows.Forms.SendKeys]::SendWait("$modPrefix$target")
        Write-Output "Pressed hotkey: $raw"
    }
    "open-app" {
        $target = $Arg1.Trim()
        $proc = Start-Process -FilePath $target -PassThru
        Write-Output "Opened app: $target (PID=$($proc.Id))"
    }
    "open-url" {
        $url = $Arg1.Trim()
        Start-Process $url | Out-Null
        Write-Output "Opened URL: $url"
    }
    "run-command" {
        $command = $Arg1
        $proc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", $command -PassThru -WindowStyle Normal
        Write-Output "Started command: $command (PID=$($proc.Id))"
    }
    "focus-window" {
        $query = $Arg1.Trim()
        $targetProc = Find-WindowTarget $query
        if ($null -eq $targetProc) {
            Write-Error "Could not find a window matching: $query"
            exit 1
        }
        [Microsoft.VisualBasic.Interaction]::AppActivate($targetProc.Id) | Out-Null
        Write-Output "Focused window: $($targetProc.ProcessName) | $($targetProc.MainWindowTitle)"
    }
    "screen-capture" {
        $targetPath = Get-ScreenshotPath $Arg1
        $targetDir = Split-Path $targetPath -Parent
        if ($targetDir -and !(Test-Path $targetDir)) {
            New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
        }
        Save-ScreenCapture $targetPath
        Write-Output $targetPath
    }
    default {
        Write-Error "Unsupported action: $Action"
        exit 1
    }
}
