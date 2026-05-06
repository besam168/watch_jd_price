#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = BASE_DIR / 'pipeline' / 'run_shakeout_dragon_capture.py'


def main() -> None:
    cmd = [sys.executable, str(MAIN_SCRIPT), '--limit', '10']
    done = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        payload = json.loads(done.stdout) if done.stdout.strip() else {}
    except Exception:
        payload = {'raw_stdout': done.stdout}
    result = {
        'returncode': done.returncode,
        'stderr': done.stderr.strip(),
        'passed_count': payload.get('passed_count'),
        'history_source': (payload.get('config') or {}).get('history_source'),
        'output_files': {
            'json': str(BASE_DIR / 'outputs' / 'shakeout_dragon_capture.json'),
            'csv': str(BASE_DIR / 'outputs' / 'shakeout_dragon_capture.csv'),
            'md': str(BASE_DIR / 'outputs' / 'shakeout_dragon_capture.md'),
        },
        'ok': done.returncode == 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if done.returncode != 0:
        raise SystemExit(done.returncode)


if __name__ == '__main__':
    main()
