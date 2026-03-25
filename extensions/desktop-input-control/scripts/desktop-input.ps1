param(
    [Parameter(Mandatory=$true)]
    [string]$Action,
    [string]$Arg1 = "",
    [string]$Arg2 = ""
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$signature = @"
using System;
using System.Runtime.InteropServices;
public static class DesktopInputNative {
  [DllImport("user32.dll")]
  public static extern bool SetCursorPos(int X, int Y);

  [DllImport("user32.dll")]
  public static extern void mouse_event(uint dwFlags, uint dx, uint dy, uint dwData, UIntPtr dwExtraInfo);
}
"@
Add-Type -TypeDefinition $signature

$MOUSEEVENTF_LEFTDOWN = 0x0002
$MOUSEEVENTF_LEFTUP = 0x0004
$MOUSEEVENTF_RIGHTDOWN = 0x0008
$MOUSEEVENTF_RIGHTUP = 0x0010

function Invoke-LeftClick {
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_LEFTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 40
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_LEFTUP, 0, 0, 0, [UIntPtr]::Zero)
}

function Invoke-RightClick {
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, [UIntPtr]::Zero)
    Start-Sleep -Milliseconds 40
    [DesktopInputNative]::mouse_event($MOUSEEVENTF_RIGHTUP, 0, 0, 0, [UIntPtr]::Zero)
}

switch ($Action) {
    "mouse-move" {
        $x = [int][math]::Round([double]$Arg1)
        $y = [int][math]::Round([double]$Arg2)
        [DesktopInputNative]::SetCursorPos($x, $y) | Out-Null
        Write-Output "Mouse moved to ($x, $y)"
    }
    "mouse-click" {
        $button = ($Arg1 | ForEach-Object { $_.ToLowerInvariant() })
        if ($button -eq "right") {
            Invoke-RightClick
            Write-Output "Mouse right click sent"
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
            if ($map.ContainsKey($single)) {
                [System.Windows.Forms.SendKeys]::SendWait($map[$single])
            } else {
                [System.Windows.Forms.SendKeys]::SendWait($single)
            }
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

        $target = if ($map.ContainsKey($last)) { $map[$last] } else { $last }
        [System.Windows.Forms.SendKeys]::SendWait("$modPrefix$target")
        Write-Output "Pressed hotkey: $raw"
    }
    default {
        Write-Error "Unsupported action: $Action"
        exit 1
    }
}
