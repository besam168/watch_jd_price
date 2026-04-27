#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime, time as dtime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PIPELINE_SCRIPT = BASE_DIR / 'pipeline' / 'run_v2.py'
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
STATE_PATH = OUTPUT_DIR / 'auto_092430_state.json'
LOG_PATH = OUTPUT_DIR / 'auto_092430.log'
HOLIDAY_PATH = Path(r'C:\Users\besam\.openclaw\workspace\skills\auction_915_925_smooth_scanner\config\cn_market_holidays.json')


def parse_args():
    parser = argparse.ArgumentParser(description='09:24:30 trigger for auction_915_925_smooth_scanner_v2.')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('--top-n', type=int, default=30)
    parser.add_argument('--earliest', default='09:24')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args()


def load_holidays():
    if not HOLIDAY_PATH.exists():
        return set()
    try:
        data = json.loads(HOLIDAY_PATH.read_text(encoding='utf-8'))
        return {str(x) for x in data if x}
    except Exception:
        return set()


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


def parse_hhmm(text: str) -> dtime:
    hour, minute = text.split(':', 1)
    return dtime(hour=int(hour), minute=int(minute))


def should_run_today(args, now: datetime, state: dict):
    today = now.strftime('%Y-%m-%d')
    if args.force:
        return True, 'force'
    if now.weekday() >= 5:
        return False, 'weekend'
    if today in load_holidays():
        return False, 'holiday'
    earliest = parse_hhmm(args.earliest)
    if now.time() < earliest:
        return False, f'before_earliest_{args.earliest}'
    if state.get('last_run_date') == today:
        return False, 'already_ran_today'
    return True, 'time_reached'


def build_command(args):
    cmd = [sys.executable, str(PIPELINE_SCRIPT), '--date', 'auto_today', '--top-n', str(args.top_n), '--json']
    if args.limit and args.limit > 0:
        cmd += ['--limit', str(args.limit)]
    return cmd


def main():
    args = parse_args()
    now = datetime.now()
    state = load_state()
    allowed, reason = should_run_today(args, now, state)
    status = {
        'checked_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'allowed': allowed,
        'reason': reason,
        'state_path': str(STATE_PATH),
        'log_path': str(LOG_PATH),
    }
    if args.dry_run or not allowed:
        print(json.dumps(status, ensure_ascii=False))
        if not allowed:
            log_line(f'SKIP reason={reason}')
        else:
            log_line('DRY_RUN allowed')
        return
    cmd = build_command(args)
    log_line('RUN ' + ' '.join(cmd))
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    run_status = {**status, 'command': cmd, 'returncode': completed.returncode, 'stdout': completed.stdout.strip(), 'stderr': completed.stderr.strip()}
    if completed.returncode == 0:
        save_state({'last_run_date': now.strftime('%Y-%m-%d'), 'last_run_at': now.strftime('%Y-%m-%d %H:%M:%S'), 'last_reason': reason, 'last_command': cmd})
        log_line(f'DONE returncode=0 stdout={completed.stdout.strip()}')
    else:
        log_line(f'FAIL returncode={completed.returncode} stderr={completed.stderr.strip()}')
    print(json.dumps(run_status, ensure_ascii=False))
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
