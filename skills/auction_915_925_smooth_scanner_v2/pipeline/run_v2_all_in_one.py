#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CAPTURE_SCRIPT = BASE_DIR / 'pipeline' / 'capture_track_v2.py'
JUDGEMENT_SCRIPT = BASE_DIR / 'pipeline' / 'run_v2_track_judgement.py'
OUTPUT_DIR = BASE_DIR / 'outputs'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_print_json(obj):
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    try:
        print(text)
    except UnicodeEncodeError:
        sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
        sys.stdout.buffer.write(b'\n')


def parse_args():
    p = argparse.ArgumentParser(description='集合竞价狙击手 V2 一体化主入口')
    p.add_argument('--limit', type=int, default=300)
    p.add_argument('--rounds', type=int, default=6)
    p.add_argument('--interval-seconds', type=int, default=5)
    p.add_argument('--top-n', type=int, default=30)
    p.add_argument('--json', action='store_true')
    return p.parse_args()


def run_cmd(cmd: list[str]) -> dict:
    done = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    return {
        'command': cmd,
        'returncode': done.returncode,
        'stdout': (done.stdout or '').strip(),
        'stderr': (done.stderr or '').strip(),
    }


def try_parse_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def main():
    args = parse_args()
    capture_cmd = [sys.executable, str(CAPTURE_SCRIPT), str(args.limit), str(args.rounds), str(args.interval_seconds)]
    cap = run_cmd(capture_cmd)
    if cap['returncode'] != 0:
        safe_print_json({'stage': 'capture', **cap})
        raise SystemExit(cap['returncode'])

    judge_cmd = [sys.executable, str(JUDGEMENT_SCRIPT), '--top-n', str(args.top_n), '--json']
    judge = run_cmd(judge_cmd)
    if judge['returncode'] != 0:
        safe_print_json({'stage': 'judgement', **judge})
        raise SystemExit(judge['returncode'])

    cap_json = try_parse_json(cap['stdout']) or {}
    judge_json = try_parse_json(judge['stdout']) or {}
    summary = {
        'plugin': 'auction_915_925_smooth_scanner_v2',
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'mode': 'all_in_one',
        'capture': cap_json,
        'judgement': judge_json,
        'compact_lines': list((judge_json.get('compact_lines') or [])),
    }
    safe_print_json(summary)


if __name__ == '__main__':
    main()
