import argparse
import json
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')


def extract_text(stdout: str) -> str:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line or not line.startswith('{'):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = str(payload.get('text') or '').strip()
        if text:
            return text
    return ''


def safe_print(text: str) -> None:
    if not text:
        return
    payload = text.rstrip() + '\n'
    try:
        sys.stdout.write(payload)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, 'encoding', None) or 'utf-8'
        repaired = payload.encode(encoding, errors='replace').decode(encoding, errors='replace')
        sys.stdout.write(repaired)
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description='Run a minimal voice roundtrip skeleton')
    parser.add_argument('wav_path', help='Path to wav file')
    parser.add_argument('--timeout-seconds', type=int, default=12)
    parser.add_argument('--culture', default='zh-CN')
    parser.add_argument('--engine', default='local_whisper', choices=['local_whisper', 'system_speech'])
    parser.add_argument('--whisper-model', default='small')
    parser.add_argument('--preprocess-mode', default='standard', choices=['standard', 'wake'])
    parser.add_argument('--echo-prefix', default='阿三收到：')
    parser.add_argument('--speak', action='store_true', help='Send reply text into TTS playback after STT succeeds')
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    transcribe_script = script_dir / 'transcribe_audio.py'
    tts_script = script_dir / 'synthesize_tts.py'
    wav_path = Path(args.wav_path).resolve()

    cmd = [
        sys.executable,
        str(transcribe_script),
        str(wav_path),
        '--timeout-seconds',
        str(args.timeout_seconds),
        '--culture',
        args.culture,
        '--engine',
        args.engine,
        '--whisper-model',
        args.whisper_model,
        '--preprocess-mode',
        args.preprocess_mode,
    ]
    completed = run_step(cmd)

    if completed.stdout:
        safe_print('=== STT RAW OUTPUT ===')
        safe_print(completed.stdout)
    if completed.stderr:
        safe_print('=== STT STDERR ===')
        safe_print(completed.stderr)

    text = extract_text(completed.stdout)
    if not text:
        safe_print('ROUNTRIP_STT_EMPTY=1')
        raise SystemExit(completed.returncode or 2)

    reply_text = f'{args.echo_prefix}{text}'
    safe_print(f'ROUNTRIP_STT_TEXT={text}')
    safe_print(f'ROUNTRIP_REPLY_TEXT={reply_text}')

    if args.speak:
        tts_completed = run_step([sys.executable, str(tts_script), reply_text])
        if tts_completed.stdout:
            safe_print('=== TTS OUTPUT ===')
            safe_print(tts_completed.stdout)
        if tts_completed.stderr:
            safe_print('=== TTS STDERR ===')
            safe_print(tts_completed.stderr)
        if tts_completed.returncode != 0:
            raise SystemExit(tts_completed.returncode)


if __name__ == '__main__':
    main()
