#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MAIN_SCRIPT = BASE_DIR / 'pipeline' / 'run_shakeout_dragon_capture.py'


def safe_print(obj) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')


def run_cmd(cmd: list[str]) -> dict:
    done = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {
        'command': cmd,
        'returncode': done.returncode,
        'stdout': (done.stdout or '').strip(),
        'stderr': (done.stderr or '').strip(),
    }


def main() -> None:
    p = argparse.ArgumentParser(description='Shakeout Dragon Capture all-in-one runner')
    p.add_argument('--limit', type=int, default=100)
    p.add_argument('--signal-offsets', default='2,3,4')
    p.add_argument('--min-up-days', type=int, default=4)
    p.add_argument('--min-volume-multiple', type=float, default=2.0)
    p.add_argument('--post-days', type=int, default=3)
    p.add_argument('--post-vol-ratio-max', type=float, default=1.0)
    p.add_argument('--post-avg-vol-ratio-max', type=float, default=0.7)
    p.add_argument('--require-limit-touch', action='store_true')
    args = p.parse_args()

    cmd = [
        sys.executable,
        str(MAIN_SCRIPT),
        '--limit', str(args.limit),
        '--signal-offsets', args.signal_offsets,
        '--min-up-days', str(args.min_up_days),
        '--min-volume-multiple', str(args.min_volume_multiple),
        '--post-days', str(args.post_days),
        '--post-vol-ratio-max', str(args.post_vol_ratio_max),
        '--post-avg-vol-ratio-max', str(args.post_avg_vol_ratio_max),
    ]
    if args.require_limit_touch:
        cmd.append('--require-limit-touch')

    result = run_cmd(cmd)
    payload = {
        'plugin': 'shakeout_dragon_capture',
        'mode': 'all_in_one',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'runner_result': result,
    }
    safe_print(payload)


if __name__ == '__main__':
    main()
