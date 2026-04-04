import ctypes
import json
import os
import subprocess
import sys
import time
import webbrowser
from ctypes import wintypes
from typing import List

try:
    import pyperclip
except Exception:
    pyperclip = None

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


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
LOG_PATH = os.path.join(LOG_DIR, "desktop-actions.jsonl")
SAFE_CONFIG_PATH = os.path.join(ROOT_DIR, "safe-config.json")
ARTIFACTS_DIR = os.path.join(ROOT_DIR, "artifacts")
LOCK_PATH = os.path.join(ROOT_DIR, "window-lock.json")


def load_safe_config():
    defaults = {
        "allowedWindowTitles": [],
        "blockedWindowTitles": ["task manager", "注册表编辑器", "registry editor"],
        "allowCommands": False,
        "allowOpenApp": True,
        "allowOpenUrl": True,
        "allowTyping": True,
        "allowHotkeys": True,
        "requireWindowMatchForInput": False,
    }
    if not os.path.exists(SAFE_CONFIG_PATH):
        return defaults
    try:
        with open(SAFE_CONFIG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            defaults.update(data)
    except Exception:
        pass
    return defaults


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)


def write_action_log(action: str, payload: dict, result: str, ok: bool = True):
    ensure_log_dir()
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "action": action,
        "payload": payload,
        "result": result,
        "ok": ok,
        "foregroundWindow": get_foreground_window_title(silent=True),
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def normalize_title(value: str) -> str:
    return (value or "").strip().lower()


def get_window_title(hwnd) -> str:
    if not hwnd:
        return ""
    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value or ""


def get_foreground_window_info():
    hwnd = user32.GetForegroundWindow()
    title = get_window_title(hwnd)
    pid = wintypes.DWORD()
    if hwnd:
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    return {
        "hwnd": int(hwnd) if hwnd else 0,
        "title": title,
        "normalizedTitle": normalize_title(title),
        "pid": int(pid.value),
    }


def get_foreground_window_title(silent: bool = False) -> str:
    return get_foreground_window_info().get("title", "")


def list_windows(query: str = ""):
    query = normalize_title(query)
    rows = []
    EnumWindows = user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    IsWindowVisible = user32.IsWindowVisible
    GetWindowThreadProcessId = user32.GetWindowThreadProcessId

    @EnumWindowsProc
    def enum_proc(hwnd, lParam):
        if not IsWindowVisible(hwnd):
            return True
        title = get_window_title(hwnd)
        if not title:
            return True
        normalized = normalize_title(title)
        if query and query not in normalized:
            return True
        pid = wintypes.DWORD()
        GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rows.append({
            "hwnd": int(hwnd),
            "title": title,
            "normalizedTitle": normalized,
            "pid": int(pid.value),
        })
        return True

    EnumWindows(enum_proc, 0)
    return rows


def find_best_window(query: str = "", pid: int = 0, prefer_foreground: bool = False):
    query = normalize_title(query)
    rows = list_windows(query)
    if pid:
        pid_rows = [row for row in rows if row.get("pid") == pid]
        if pid_rows:
            rows = pid_rows
        else:
            return None
    if not rows:
        return None

    fg = get_foreground_window_info()
    fg_hwnd = int(fg.get("hwnd") or 0)
    fg_pid = int(fg.get("pid") or 0)
    fg_title = normalize_title(str(fg.get("title") or ""))

    if prefer_foreground:
        for row in rows:
            if int(row.get("hwnd") or 0) == fg_hwnd and fg_hwnd:
                return row
        for row in rows:
            if int(row.get("pid") or 0) == fg_pid and fg_pid:
                return row
        for row in rows:
            title = normalize_title(str(row.get("title") or ""))
            if fg_title and title == fg_title:
                return row

    exact_title_rows = [row for row in rows if normalize_title(str(row.get("title") or "")) == query]
    if exact_title_rows:
        return exact_title_rows[-1]

    exact_pid_title_rows = [
        row for row in rows
        if pid and int(row.get("pid") or 0) == pid and normalize_title(str(row.get("title") or "")) == query
    ]
    if exact_pid_title_rows:
        return exact_pid_title_rows[-1]

    return rows[-1]


def create_artifact_prefix(name: str):
    ensure_log_dir()
    stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_") else "-" for ch in (name or "artifact"))
    return os.path.join(ARTIFACTS_DIR, f"{stamp}-{safe}")


def read_window_lock():
    if not os.path.exists(LOCK_PATH):
        return None
    try:
        with open(LOCK_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def resolve_window_lock(title: str = "", pid: int = 0, foreground: bool = False):
    if foreground:
        fg = get_foreground_window_info()
        if not fg.get("hwnd"):
            raise RuntimeError("Could not resolve foreground window")
        return {"title": fg.get("title"), "pid": fg.get("pid"), "hwnd": fg.get("hwnd"), "mode": "foreground"}

    title = (title or "").strip()
    if not title and not pid:
        raise ValueError("title or pid is required unless foreground=true")

    match = find_best_window(title, pid, prefer_foreground=True)
    if not match:
        raise RuntimeError(f"Could not find a window matching: {title or pid}")
    return {"title": match.get("title"), "pid": match.get("pid"), "hwnd": match.get("hwnd"), "mode": "query"}


def write_window_lock(data: dict | None):
    if not data:
        if os.path.exists(LOCK_PATH):
            os.remove(LOCK_PATH)
        return
    with open(LOCK_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def enforce_window_guard(config: dict, action: str):
    title = get_foreground_window_title(silent=True)
    normalized = normalize_title(title)

    blocked = [normalize_title(x) for x in config.get("blockedWindowTitles", []) if normalize_title(x)]
    for item in blocked:
        if item and item in normalized:
            raise PermissionError(f"Action blocked on foreground window: {title}")

    lock = read_window_lock()
    if lock:
        fg = get_foreground_window_info()
        lock_title = normalize_title(str(lock.get("title") or ""))
        lock_pid = int(lock.get("pid") or 0)
        lock_hwnd = int(lock.get("hwnd") or 0)
        current_title = normalize_title(str(fg.get("title") or ""))
        current_pid = int(fg.get("pid") or 0)
        current_hwnd = int(fg.get("hwnd") or 0)
        title_ok = bool(lock_title and lock_title == current_title)
        pid_ok = bool(lock_pid and current_pid == lock_pid)
        hwnd_ok = bool(lock_hwnd and current_hwnd == lock_hwnd)
        if not (hwnd_ok or (pid_ok and title_ok) or pid_ok):
            raise PermissionError(f"Foreground window violates active lock for action {action}: {title}")

    if config.get("requireWindowMatchForInput"):
        allowed = [normalize_title(x) for x in config.get("allowedWindowTitles", []) if normalize_title(x)]
        if allowed and not any(item in normalized for item in allowed):
            raise PermissionError(f"Foreground window not allowed for action {action}: {title}")


def recent_action_log(limit: int = 20):
    if not os.path.exists(LOG_PATH):
        return []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()[-max(1, limit):]
    rows = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            rows.append({"raw": line})
    return rows


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


def set_clipboard_text(text: str):
    if pyperclip is None:
        raise RuntimeError("pyperclip is not installed")
    pyperclip.copy(text)
    return f"Clipboard text set ({len(text)} chars)"


def load_text_payload(raw: str):
    value = raw or ""
    if value.startswith("@file:"):
        path = value[len("@file:"):]
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return value


def paste_text(text: str):
    if pyperclip is None:
        raise RuntimeError("pyperclip is not installed")
    resolved = load_text_payload(text)
    pyperclip.copy(resolved)
    press_hotkey("ctrl+v")
    return f"Pasted text via clipboard: {resolved}"


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


def resolve_focus_target(query: str = "", pid: int = 0, foreground: bool = False):
    query = (query or "").strip().lower()
    if foreground or query in {"foreground", "current", "active", "fg"}:
        info = get_foreground_window_info()
        hwnd = int(info.get("hwnd") or 0)
        title = str(info.get("title") or "")
        target_pid = int(info.get("pid") or 0)
        if not hwnd:
            raise RuntimeError("Could not resolve foreground window")
        return {
            "query": query,
            "foreground": True,
            "hwnd": hwnd,
            "title": title,
            "pid": target_pid,
        }

    if not query and not pid:
        raise ValueError("title or pid is required")
    match = find_best_window(query, pid, prefer_foreground=True)
    if not match:
        raise RuntimeError(f"Could not find a window matching: {query or pid}")
    return {
        "query": query,
        "foreground": False,
        "hwnd": int(match["hwnd"]),
        "title": str(match["title"]),
        "pid": int(match.get("pid") or 0),
    }


def try_focus_window(hwnd: int, title: str):
    strategies = []

    def strategy_restore_foreground():
        user32.ShowWindow(hwnd, SW_RESTORE)
        return bool(user32.SetForegroundWindow(hwnd))

    strategies.append(("restore+set-foreground", strategy_restore_foreground))

    def strategy_restore_bring_top():
        user32.ShowWindow(hwnd, SW_RESTORE)
        user32.BringWindowToTop(hwnd)
        return bool(user32.SetForegroundWindow(hwnd))

    strategies.append(("restore+bring-to-top+set-foreground", strategy_restore_bring_top))

    def strategy_attach_thread_input():
        current_thread_id = kernel32.GetCurrentThreadId()
        target_thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        foreground_hwnd = user32.GetForegroundWindow()
        foreground_thread_id = user32.GetWindowThreadProcessId(foreground_hwnd, None) if foreground_hwnd else 0

        attached_target = False
        attached_foreground = False
        try:
            if target_thread_id and target_thread_id != current_thread_id:
                attached_target = bool(user32.AttachThreadInput(current_thread_id, target_thread_id, True))
            if foreground_thread_id and foreground_thread_id != current_thread_id and foreground_thread_id != target_thread_id:
                attached_foreground = bool(user32.AttachThreadInput(current_thread_id, foreground_thread_id, True))
            user32.ShowWindow(hwnd, SW_RESTORE)
            user32.BringWindowToTop(hwnd)
            user32.SetActiveWindow(hwnd)
            user32.SetFocus(hwnd)
            return bool(user32.SetForegroundWindow(hwnd))
        finally:
            if attached_foreground:
                user32.AttachThreadInput(current_thread_id, foreground_thread_id, False)
            if attached_target:
                user32.AttachThreadInput(current_thread_id, target_thread_id, False)

    strategies.append(("attach-thread-input", strategy_attach_thread_input))

    errors = []
    for name, fn in strategies:
        try:
            call_ok = bool(fn())
            if call_ok:
                return {"ok": True, "strategy": name, "errors": errors}
            errors.append({"strategy": name, "error": f"SetForegroundWindow returned false for: {title}"})
        except Exception as exc:
            errors.append({"strategy": name, "error": str(exc)})

    return {"ok": False, "strategy": None, "errors": errors}


def focus_window(query: str = "", pid: int = 0, foreground: bool = False):
    target = resolve_focus_target(query, pid, foreground=foreground)
    focus_attempt = try_focus_window(target["hwnd"], target["title"])
    if not focus_attempt.get("ok"):
        raise RuntimeError(json.dumps({
            "error": f"Failed to focus window: {target['title']}",
            "focusStrategy": None,
            "focusErrors": focus_attempt.get("errors", []),
        }, ensure_ascii=False))
    return json.dumps({
        "ok": True,
        "title": target["title"],
        "pid": target["pid"],
        "hwnd": target["hwnd"],
        "focusStrategy": focus_attempt.get("strategy"),
        "focusErrors": focus_attempt.get("errors", []),
    }, ensure_ascii=False)


def focus_window_verified(query: str = "", pid: int = 0, foreground: bool = False, retries: int = 2, verify_delay_ms: int = 250):
    query = (query or "").strip().lower()
    target = resolve_focus_target(query, pid, foreground=foreground)
    expected = {
        "hwnd": int(target.get("hwnd") or 0),
        "title": str(target.get("title") or ""),
        "normalizedTitle": normalize_title(str(target.get("title") or "")),
        "pid": int(target.get("pid") or 0),
    }

    retries = max(0, int(retries))
    verify_delay_ms = max(0, int(verify_delay_ms))
    attempts = []
    final_info = None
    success_focus_strategy = None

    for attempt in range(retries + 1):
        focus_attempt = try_focus_window(expected["hwnd"], expected["title"])
        call_ok = bool(focus_attempt.get("ok"))
        call_error = None
        if not call_ok:
            call_error = json.dumps({
                "error": f"Failed to focus window: {expected['title']}",
                "focusStrategy": None,
                "focusErrors": focus_attempt.get("errors", []),
            }, ensure_ascii=False)

        if verify_delay_ms > 0:
            time.sleep(verify_delay_ms / 1000.0)

        final_info = get_foreground_window_info()
        expected_hwnd = int(expected.get("hwnd") or 0)
        expected_pid = int(expected.get("pid") or 0)
        expected_title = normalize_title(str(expected.get("title") or ""))
        actual_hwnd = int(final_info.get("hwnd") or 0)
        actual_pid = int(final_info.get("pid") or 0)
        actual_title = normalize_title(str(final_info.get("title") or ""))
        success = bool(
            (expected_hwnd and expected_hwnd == actual_hwnd)
            or (expected_pid and expected_pid == actual_pid)
            or (expected_title and expected_title == actual_title)
        )
        attempt_result = {
            "attempt": attempt + 1,
            "callOk": call_ok,
            "callError": call_error,
            "focusStrategy": focus_attempt.get("strategy"),
            "focusErrors": focus_attempt.get("errors", []),
            "actual": final_info,
            "success": success,
        }
        attempts.append(attempt_result)
        if success:
            success_focus_strategy = focus_attempt.get("strategy")
            return {
                "ok": True,
                "query": query or None,
                "pid": int(pid or 0),
                "foreground": bool(target.get("foreground")),
                "retries": retries,
                "verifyDelayMs": verify_delay_ms,
                "expected": expected,
                "actual": final_info,
                "focusStrategy": success_focus_strategy,
                "attempts": attempts,
            }

    return {
        "ok": False,
        "error": "focus verification failed",
        "query": query or None,
        "pid": int(pid or 0),
        "foreground": bool(target.get("foreground")),
        "retries": retries,
        "verifyDelayMs": verify_delay_ms,
        "expected": expected,
        "actual": final_info,
        "focusStrategy": success_focus_strategy,
        "attempts": attempts,
    }


def emit(text: str):
    sys.stdout.write(text)
    sys.stdout.flush()


def main(argv):
    if len(argv) < 2:
        raise ValueError("action is required")
    action = argv[1]
    args = argv[2:] + [""] * 4
    arg1, arg2, arg3, arg4 = args[:4]
    config = load_safe_config()

    if action == "get-foreground-window":
        emit(get_foreground_window_title(silent=True))
        return 0
    if action == "get-foreground-window-info":
        emit(json.dumps(get_foreground_window_info(), ensure_ascii=False))
        return 0
    if action == "list-windows":
        emit(json.dumps(list_windows(arg1 or ""), ensure_ascii=False))
        return 0
    if action == "get-window-lock":
        emit(json.dumps(read_window_lock(), ensure_ascii=False))
        return 0
    if action == "set-window-lock":
        raw_args = [str(x or "").strip() for x in argv[2:]]
        truthy = {"true", "yes", "foreground", "fg"}
        falsy = {"false", "no"}

        title = raw_args[0] if len(raw_args) >= 1 else ""
        pid = int(raw_args[1]) if len(raw_args) >= 2 and str(raw_args[1]).isdigit() else 0
        foreground = False
        if len(raw_args) >= 3:
            flag = raw_args[2].lower()
            if flag in truthy:
                foreground = True
            elif flag in falsy:
                foreground = False
        elif title.lower() in truthy:
            foreground = True
            title = ""

        lock = resolve_window_lock(title=title, pid=pid, foreground=foreground)
        write_window_lock(lock)
        emit(json.dumps(lock, ensure_ascii=False))
        return 0
    if action == "clear-window-lock":
        write_window_lock(None)
        emit("Window lock cleared")
        return 0
    if action == "get-recent-actions":
        limit = max(1, int(arg1 or "20"))
        emit(json.dumps(recent_action_log(limit), ensure_ascii=False))
        return 0
    if action == "mouse-move":
        enforce_window_guard(config, action)
        x = round(float(arg1))
        y = round(float(arg2))
        set_cursor_pos(x, y)
        result = f"Mouse moved to ({x}, {y})"
        write_action_log(action, {"x": x, "y": y}, result)
        emit(result)
        return 0
    if action == "mouse-move-relative":
        enforce_window_guard(config, action)
        dx = round(float(arg1))
        dy = round(float(arg2))
        x, y = get_cursor_pos()
        nx, ny = x + dx, y + dy
        set_cursor_pos(nx, ny)
        result = f"Mouse moved relatively by ({dx}, {dy}) to ({nx}, {ny})"
        write_action_log(action, {"dx": dx, "dy": dy, "x": nx, "y": ny}, result)
        emit(result)
        return 0
    if action == "mouse-click":
        enforce_window_guard(config, action)
        result = mouse_click(arg1 or "left")
        write_action_log(action, {"button": arg1 or "left"}, result)
        emit(result)
        return 0
    if action == "mouse-drag":
        enforce_window_guard(config, action)
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
        result = f"Mouse dragged from ({x1}, {y1}) to ({x2}, {y2})"
        write_action_log(action, {"fromX": x1, "fromY": y1, "toX": x2, "toY": y2}, result)
        emit(result)
        return 0
    if action == "mouse-scroll":
        enforce_window_guard(config, action)
        delta = -240 if arg1 == "down" else 240 if arg1 == "up" else round(float(arg1))
        user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, ctypes.c_uint32(ctypes.c_int32(delta).value).value, 0)
        result = f"Mouse wheel scrolled by {delta}"
        write_action_log(action, {"delta": delta}, result)
        emit(result)
        return 0
    if action == "type-text":
        if not config.get("allowTyping", True):
            raise PermissionError("Typing is disabled by safe-config")
        enforce_window_guard(config, action)
        result = type_text(arg1)
        write_action_log(action, {"text": arg1}, result)
        emit(result)
        return 0
    if action == "set-clipboard-text":
        result = set_clipboard_text(arg1)
        write_action_log(action, {"text": arg1}, result)
        emit(result)
        return 0
    if action == "paste-text":
        if not config.get("allowTyping", True):
            raise PermissionError("Typing is disabled by safe-config")
        enforce_window_guard(config, action)
        result = paste_text(arg1)
        write_action_log(action, {"text": arg1}, result)
        emit(result)
        return 0
    if action == "press-hotkey":
        if not config.get("allowHotkeys", True):
            raise PermissionError("Hotkeys are disabled by safe-config")
        enforce_window_guard(config, action)
        result = press_hotkey(arg1)
        write_action_log(action, {"keys": arg1}, result)
        emit(result)
        return 0
    if action == "open-app":
        if not config.get("allowOpenApp", True):
            raise PermissionError("Open-app is disabled by safe-config")
        result = open_app(arg1)
        write_action_log(action, {"target": arg1}, result)
        emit(result)
        return 0
    if action == "open-url":
        if not config.get("allowOpenUrl", True):
            raise PermissionError("Open-url is disabled by safe-config")
        result = open_url(arg1)
        write_action_log(action, {"url": arg1}, result)
        emit(result)
        return 0
    if action == "run-command":
        if not config.get("allowCommands", False):
            raise PermissionError("Run-command is disabled by safe-config")
        result = run_command(arg1)
        write_action_log(action, {"command": arg1}, result)
        emit(result)
        return 0
    if action in {"focus-window", "focus-window-verified"}:
        raw_args = [str(x or "").strip() for x in argv[2:]]
        truthy = {"true", "yes", "foreground", "fg", "current", "active"}
        falsy = {"false", "no"}
        title = raw_args[0] if len(raw_args) >= 1 else ""
        pid = int(raw_args[1]) if len(raw_args) >= 2 and str(raw_args[1]).isdigit() else 0
        retries = int(raw_args[2]) if len(raw_args) >= 3 and str(raw_args[2]).isdigit() else 2
        verify_delay_ms = int(raw_args[3]) if len(raw_args) >= 4 and str(raw_args[3]).isdigit() else 250
        foreground = False
        if len(raw_args) >= 5:
            flag = raw_args[4].lower()
            if flag in truthy:
                foreground = True
            elif flag in falsy:
                foreground = False
        elif title.lower() in truthy:
            foreground = True
            title = ""

        if action == "focus-window-verified":
            result_obj = focus_window_verified(title, pid, foreground=foreground, retries=retries, verify_delay_ms=verify_delay_ms)
            write_action_log(action, {"title": title, "pid": pid, "foreground": foreground, "retries": retries, "verifyDelayMs": verify_delay_ms}, json.dumps(result_obj, ensure_ascii=False), ok=bool(result_obj.get("ok")))
            emit(json.dumps(result_obj, ensure_ascii=False))
            return 0 if result_obj.get("ok") else 1

        result = focus_window(title, pid, foreground=foreground)
        write_action_log(action, {"title": title, "pid": pid, "foreground": foreground}, result)
        emit(result)
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
