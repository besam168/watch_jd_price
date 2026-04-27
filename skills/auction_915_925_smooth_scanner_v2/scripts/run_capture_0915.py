#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAPTURE_SCRIPT = BASE_DIR / 'pipeline' / 'capture_track_v2.py'
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = OUTPUT_DIR / 'capture_0915_state.json'
LOG_PATH = OUTPUT_DIR / 'capture_0915.log'


def parse_args():
    p = argparse.ArgumentParser(description='09:15 启动集合竞价轨迹采样')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--rounds', type=int, default=115)
    p.add_argument('--interval-seconds', type=int, default=5)
    p.add_argument('--force', action='store_true')
    return p.parse_args()


def load_state():
    if not STATE_PATH.exists():
        return {}
    try:
        return json.loads(STATE_PATH.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_state(obj: dict):
    STATE_PATH.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def log_line(message: str):
    stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with LOG_PATH.open('a', encoding='utf-8') as f:
        f.write(f'[{stamp}] {message}\n')


def main():
    args = parse_args()
    today = datetime.now().strftime('%Y-%m-%d')
    state = load_state()
    if not args.force and state.get('last_run_date') == today:
        print(json.dumps({'skipped': True, 'reason': 'already_ran_today', 'date': today}, ensure_ascii=False))
        return
    cmd = [sys.executable, str(CAPTURE_SCRIPT), str(args.limit), str(args.rounds), str(args.interval_seconds)]
    log_line('RUN ' + ' '.join(cmd))
    done = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    payload = {
        'date': today,
        'command': cmd,
        'returncode': done.returncode,
        'stdout': (done.stdout or '').strip(),
        'stderr': (done.stderr or '').strip(),
    }
    if done.returncode == 0:
        save_state({'last_run_date': today, 'last_run_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        log_line('DONE ' + payload['stdout'])
    else:
        log_line('FAIL ' + payload['stderr'])
        raise SystemExit(done.returncode)
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == '__main__':
    main()
