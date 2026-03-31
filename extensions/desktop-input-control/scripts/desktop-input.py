import ctypes
import json
import os
import subprocess
import sys
import time
import webbrowser
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_SCANCODE = 0x0008
SW_RESTORE = 9

VK_MAP = {
    "ctrl": 0x11,
    "control": 0x11,
    "alt": 0x12,
    "shift": 0x10,
    "win": 0x5B,
    "enter": 0x0D,
    "tab": 0x09,
    "esc": 0x1B,
    "escape": 0x1B,
    "delete": 0x2E,
    "backspace": 0x08,
    "space": 0x20,
    "up": 0x26,
    "down": 0x28,
    "left": 0x25,
    "right": 0x27,
    "home": 0x24,
    "end": 0x23,
    "pageup": 0x21,
    "pagedown": 0x22,
    "insert": 0x2D,
    "capslock": 0x14,
    "printscreen": 0x2C,
}
for i in range(1, 13):
    VK_MAP[f"f{i}"] = 0x6F + i
for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    VK_MAP[c.lower()] = ord(c)
for d in "0123456789":
    VK_MAP[d] = ord(d)

ULONG_PTR = wintypes.WPARAM

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", INPUT_UNION)]

class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def send_input(*inputs):
    arr = (INPUT * len(inputs))(*inputs)
    sent = user32.SendInput(len(inputs), ctypes.byref(arr), ctypes.sizeof(INPUT))
    if sent != len(inputs):
        raise OSError(f"SendInput failed: sent {sent}/{len(inputs)}")


def keyboard_vk(vk: int, keyup: bool = False):
    flags = KEYEVENTF_KEYUP if keyup else 0
    return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=vk, wScan=0, dwFlags=flags, time=0, dwExtraInfo=0)))


def keyboard_unicode(ch: str, keyup: bool = False):
    flags = KEYEVENTF_UNICODE | (KEYEVENTF_KEYUP if keyup else 0)
    return INPUT(type=INPUT_KEYBOARD, union=INPUT_UNION(ki=KEYBDINPUT(wVk=0, wScan=ord(ch), dwFlags=flags, time=0, dwExtraInfo=0)))


def get_cursor_pos():
    pt = POINT()
    if not user32.GetCursorPos(ctypes.byref(pt)):
        raise OSError("GetCursorPos failed")
    return pt.x, pt.y


def set_cursor_pos(x: int, y: int):
    if not user32.SetCursorPos(int(x), int(y)):
        raise OSError("SetCursorPos failed")


def mouse_click(button: str):
    button = (button or "left").lower()
    if button == "right":
        user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        return "Mouse right click sent"
    if button == "middle":
        user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
        time.sleep(0.04)
        user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
        return "Mouse middle click sent"
    if button == "double":
        mouse_click("left")
        time.sleep(0.08)
        mouse_click("left")
        return "Mouse double click sent"
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.04)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    return "Mouse left click sent"


def type_text(text: str):
    inputs = []
    for ch in text:
        inputs.append(keyboard_unicode(ch, False))
        inputs.append(keyboard_unicode(ch, True))
    if inputs:
        send_input(*inputs)
    return f"Typed text: {text}"


def press_hotkey(keys: str):
    raw = (keys or "").strip().lower()
    if not raw:
        raise ValueError("keys is required")
    parts = [p.strip() for p in raw.split("+") if p.strip()]
    if not parts:
        raise ValueError("invalid keys")
    modifiers = []
    normal = []
    for part in parts:
        if part in {"ctrl", "control", "alt", "shift", "win"}:
            modifiers.append(part)
        else:
            normal.append(part)
    if not normal and modifiers:
        normal = [modifiers.pop()]
    vk_sequence = []
    for part in modifiers + normal:
        vk = VK_MAP.get(part)
        if vk is None:
            if len(part) == 1:
                vk = VK_MAP.get(part.lower())
            if vk is None:
                raise ValueError(f"unsupported key: {part}")
        vk_sequence.append((part, vk))
    down_inputs = [keyboard_vk(vk, False) for _, vk in vk_sequence]
    up_inputs = [keyboard_vk(vk, True) for _, vk in reversed(vk_sequence)]
    send_input(*(down_inputs + up_inputs))
    return f"Pressed hotkey: {raw}"


def open_app(target: str):
    target = (target or "").strip()
    if not target:
        raise ValueError("target is required")
    try:
        proc = subprocess.Popen(target)
        return f"Opened app: {target} (PID={proc.pid})"
    except Exception:
        os.startfile(target)
        return f"Opened app: {target}"


def open_url(url: str):
    url = (url or "").strip()
    if not url:
        raise ValueError("url is required")
    webbrowser.open(url)
    return f"Opened URL: {url}"


def run_command(command: str):
    proc = subprocess.Popen(["cmd.exe", "/c", command], creationflags=0)
    return f"Started command: {command} (PID={proc.pid})"


def focus_window(query: str):
    query = (query or "").strip().lower()
    if not query:
        raise ValueError("title is required")
    matches = []

    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    GetWindowTextLength = user32.GetWindowTextLengthW
    GetWindowText = user32.GetWindowTextW
    IsWindowVisible = user32.IsWindowVisible
    ShowWindow = user32.ShowWindow
    SetForegroundWindow = user32.SetForegroundWindow

    @EnumWindowsProc
    def enum_proc(hwnd, lParam):
        if not IsWindowVisible(hwnd):
            return True
        length = GetWindowTextLength(hwnd)
        if length <= 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        GetWindowText(hwnd, buf, length + 1)
        title = buf.value or ""
        if query in title.lower():
            matches.append((hwnd, title))
        return True

    EnumWindows(enum_proc, 0)
    if not matches:
        raise RuntimeError(f"Could not find a window matching: {query}")
    hwnd, title = matches[-1]
    ShowWindow(hwnd, SW_RESTORE)
    if not SetForegroundWindow(hwnd):
        raise RuntimeError(f"Failed to focus window: {title}")
    return f"Focused window: {title}"


def emit(text: str):
    sys.stdout.write(text)
    sys.stdout.flush()


def main(argv):
    if len(argv) < 2:
        raise ValueError("action is required")
    action = argv[1]
    args = argv[2:] + [""] * 4
    arg1, arg2, arg3, arg4 = args[:4]

    if action == "mouse-move":
        x = round(float(arg1))
        y = round(float(arg2))
        set_cursor_pos(x, y)
        emit(f"Mouse moved to ({x}, {y})")
        return 0
    if action == "mouse-move-relative":
        dx = round(float(arg1))
        dy = round(float(arg2))
        x, y = get_cursor_pos()
        nx, ny = x + dx, y + dy
        set_cursor_pos(nx, ny)
        emit(f"Mouse moved relatively by ({dx}, {dy}) to ({nx}, {ny})")
        return 0
    if action == "mouse-click":
        emit(mouse_click(arg1 or "left"))
        return 0
    if action == "mouse-drag":
        x1 = round(float(arg1))
        y1 = round(float(arg2))
        x2 = round(float(arg3))
        y2 = round(float(arg4))
        set_cursor_pos(x1, y1)
        time.sleep(0.06)
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.08)
        set_cursor_pos(x2, y2)
        time.sleep(0.08)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        emit(f"Mouse dragged from ({x1}, {y1}) to ({x2}, {y2})")
        return 0
    if action == "mouse-scroll":
        delta = -240 if arg1 == "down" else 240 if arg1 == "up" else round(float(arg1))
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, ctypes.c_uint32(ctypes.c_int32(delta).value).value, 0)
        emit(f"Mouse wheel scrolled by {delta}")
        return 0
    if action == "type-text":
        emit(type_text(arg1))
        return 0
    if action == "press-hotkey":
        emit(press_hotkey(arg1))
        return 0
    if action == "open-app":
        emit(open_app(arg1))
        return 0
    if action == "open-url":
        emit(open_url(arg1))
        return 0
    if action == "run-command":
        emit(run_command(arg1))
        return 0
    if action == "focus-window":
        emit(focus_window(arg1))
        return 0
    if action == "screen-capture":
        raise ValueError("screen-capture action moved to screen-capture-compat.ps1")
    raise ValueError(f"Unsupported action: {action}")


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv))
    except Exception as exc:
        sys.stderr.write(str(exc))
        sys.stderr.flush()
        raise SystemExit(1)
