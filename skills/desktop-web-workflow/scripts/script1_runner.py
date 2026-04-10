import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESKTOP_INPUT = ROOT / 'extensions' / 'desktop-input-control' / 'scripts' / 'desktop-input.py'
OUTPUT_DIR = ROOT / 'skills' / 'desktop-web-workflow' / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_TITLE_QUERY = 'OpenClaw Control'
REL_X = 833
REL_Y = 943
MESSAGE = '继续'


def run_action(*args):
    cmd = ['python', str(DESKTOP_INPUT), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {
        'cmd': cmd,
        'returncode': proc.returncode,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def get_window_hwnd():
    result = run_action('list-windows', WINDOW_TITLE_QUERY)
    if result['returncode'] != 0:
        raise RuntimeError(result['stderr'] or result['stdout'] or 'list-windows failed')
    rows = json.loads(result['stdout'] or '[]')
    if not rows:
        raise RuntimeError('OpenClaw window not found')
    return int(rows[-1]['hwnd'])


def get_window_rect(hwnd: int):
    script = (
        'import ctypes, json; '
        'from ctypes import wintypes; '
        f'hwnd={hwnd}; '
        'rect=wintypes.RECT(); '
        'ok=ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)); '
        'print(json.dumps({"ok": bool(ok), "left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom, '
        '"width": rect.right-rect.left, "height": rect.bottom-rect.top}))'
    )
    proc = subprocess.run(['python', '-c', script], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or 'GetWindowRect failed')
    data = json.loads(proc.stdout.strip())
    if not data.get('ok'):
        raise RuntimeError('GetWindowRect returned false')
    return data


def main():
    message = MESSAGE
    if len(sys.argv) > 1:
        message = sys.argv[1]

    stamp = time.strftime('%Y%m%d_%H%M%S')
    run_dir = OUTPUT_DIR / f'script1_relative_{stamp}'
    run_dir.mkdir(parents=True, exist_ok=True)

    log = {
        'startedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'mode': 'window-relative',
        'windowQuery': WINDOW_TITLE_QUERY,
        'relativePoint': {'x': REL_X, 'y': REL_Y},
        'message': message,
        'steps': []
    }

    try:
        hwnd = get_window_hwnd()
        rect = get_window_rect(hwnd)
        target_x = rect['left'] + REL_X
        target_y = rect['top'] + REL_Y

        log['steps'].append({'step': 'resolve-window', 'hwnd': hwnd, 'rect': rect, 'target': {'x': target_x, 'y': target_y}})
        log['steps'].append({'step': 'move-mouse', 'result': run_action('mouse-move', str(target_x), str(target_y))})
        time.sleep(0.2)
        log['steps'].append({'step': 'click-target', 'result': run_action('mouse-click', 'left')})
        time.sleep(0.25)
        log['steps'].append({'step': 'type-text', 'result': run_action('type-text', message)})
        time.sleep(0.2)
        log['steps'].append({'step': 'press-enter', 'result': run_action('press-hotkey', 'enter')})
        log['status'] = 'ok'
    except Exception as exc:
        log['status'] = 'error'
        log['error'] = str(exc)

    log['finishedAt'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    out = run_dir / 'run-log.json'
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))


if __name__ == '__main__':
    main()
