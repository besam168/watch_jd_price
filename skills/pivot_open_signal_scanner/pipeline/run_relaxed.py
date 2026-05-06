#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MAIN = BASE_DIR / 'pipeline' / 'run_shakeout_dragon_capture.py'
cmd = [
    sys.executable, str(MAIN),
    '--limit', '300',
    '--min-up-days', '3',
    '--min-volume-multiple', '1.7',
    '--post-avg-vol-ratio-max', '0.85',
]
raise SystemExit(subprocess.run(cmd).returncode)
