import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DESKTOP_INPUT = ROOT / 'extensions' / 'desktop-input-control' / 'scripts' / 'desktop-input.py'
OUTPUT_DIR = ROOT / 'skills' / 'desktop-web-workflow' / 'output'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_action(*args):
    cmd = ['python', str(DESKTOP_INPUT), *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {
        'cmd': cmd,
        'returncode': proc.returncode,
        'stdout': proc.stdout.strip(),
        'stderr': proc.stderr.strip(),
    }


def main():
    message = '继续'
    if len(sys.argv) > 1:
        message = sys.argv[1]

    stamp = time.strftime('%Y%m%d_%H%M%S')
    run_dir = OUTPUT_DIR / f'script1_{stamp}'
    run_dir.mkdir(parents=True, exist_ok=True)

    log = {
        'startedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'mode': 'light-no-focus',
        'message': message,
        'steps': []
    }

    log['steps'].append({'step': 'click-current-position', 'result': run_action('mouse-click', 'left')})
    time.sleep(0.25)
    log['steps'].append({'step': 'type-text', 'result': run_action('type-text', message)})
    time.sleep(0.2)
    log['steps'].append({'step': 'press-enter', 'result': run_action('press-hotkey', 'enter')})
    log['finishedAt'] = time.strftime('%Y-%m-%dT%H:%M:%S')

    out = run_dir / 'run-log.json'
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))


if __name__ == '__main__':
    main()
