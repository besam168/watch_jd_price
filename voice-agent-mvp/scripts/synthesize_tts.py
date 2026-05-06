from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def safe_write(text: str, *, is_error: bool = False) -> None:
    if not text:
        return
    stream = sys.stderr if is_error else sys.stdout
    payload = text.rstrip() + "\n"
    try:
        stream.write(payload)
    except UnicodeEncodeError:
        encoding = getattr(stream, 'encoding', None) or 'utf-8'
        repaired = payload.encode(encoding, errors='replace').decode(encoding, errors='replace')
        stream.write(repaired)
    stream.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description='Synthesize reply text to audio and play it through the local speaker backend')
    parser.add_argument('text', help='Text to speak')
    parser.add_argument(
        '--config',
        default=str(Path(__file__).resolve().parents[2] / 'skills' / 'tmall-genie-voice-bridge' / 'config.local-speaker.json'),
        help='Path to speak config JSON file',
    )
    args = parser.parse_args()

    speak_script = Path(__file__).resolve().parents[2] / 'skills' / 'tmall-genie-voice-bridge' / 'scripts' / 'speak.py'
    config_path = Path(args.config).resolve()
    if not speak_script.is_file():
        safe_write(f'TTS_SCRIPT_NOT_FOUND {speak_script}', is_error=True)
        return 1
    if not config_path.is_file():
        safe_write(f'TTS_CONFIG_NOT_FOUND {config_path}', is_error=True)
        return 1

    cmd = [
        sys.executable,
        str(speak_script),
        args.text,
        '--config',
        str(config_path),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if completed.stdout:
        safe_write(completed.stdout)
    if completed.stderr:
        safe_write(completed.stderr, is_error=True)
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
