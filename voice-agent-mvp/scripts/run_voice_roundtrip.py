import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path


def run_step(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')


def load_result_payload(result_json_path: Path | None) -> dict:
    if not result_json_path or not result_json_path.is_file():
        return {}
    try:
        payload = json.loads(result_json_path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def extract_text(stdout: str, result_json_path: Path | None = None) -> str:
    payload = load_result_payload(result_json_path)
    if payload:
        text = str(payload.get('text') or '').strip()
        if text:
            return text
        text_b64 = str(payload.get('text_b64') or '').strip()
        if text_b64:
            try:
                decoded = base64.b64decode(text_b64).decode('utf-8').strip()
            except Exception:
                decoded = ''
            if decoded:
                return decoded

    decoder = json.JSONDecoder()
    idx = 0
    payloads: list[dict] = []
    while idx < len(stdout):
        start = stdout.find('{', idx)
        if start == -1:
            break
        try:
            payload, end = decoder.raw_decode(stdout[start:])
        except json.JSONDecodeError:
            idx = start + 1
            continue
        if isinstance(payload, dict):
            payloads.append(payload)
        idx = start + end

    for payload in reversed(payloads):
        text = str(payload.get('text') or '').strip()
        if text and set(text) != {'?'}:
            return text
        text_b64 = str(payload.get('text_b64') or '').strip()
        if text_b64:
            try:
                decoded = base64.b64decode(text_b64).decode('utf-8').strip()
            except Exception:
                decoded = ''
            if decoded:
                return decoded
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
    result_json_path = script_dir.parent / 'output' / 'last_stt_result.json'

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
        '--result-json',
        str(result_json_path),
    ]
    completed = run_step(cmd)
    payload = load_result_payload(result_json_path)

    if completed.stdout:
        safe_print('=== STT RAW OUTPUT ===')
        safe_print(completed.stdout)
    if completed.stderr:
        safe_print('=== STT STDERR ===')
        safe_print(completed.stderr)
    if payload:
        safe_print(f'STT_RESULT_JSON={result_json_path}')
        text_b64 = str(payload.get('text_b64') or '').strip()
        if text_b64:
            safe_print(f'STT_TEXT_B64={text_b64}')

    text = extract_text(completed.stdout, result_json_path)
    if not text:
        safe_print('ROUNTRIP_STT_EMPTY=1')
        raise SystemExit(completed.returncode or 2)

    reply_text = f'{args.echo_prefix}{text}'
    reply_json_path = script_dir.parent / 'output' / 'last_roundtrip_reply.json'
    reply_payload = {
        'ok': True,
        'stt_text': text,
        'stt_text_b64': base64.b64encode(text.encode('utf-8')).decode('ascii'),
        'reply_text': reply_text,
        'reply_text_b64': base64.b64encode(reply_text.encode('utf-8')).decode('ascii'),
        'result_json_path': str(result_json_path),
        'wav_path': str(wav_path),
        'engine': args.engine,
        'whisper_model': args.whisper_model,
        'preprocess_mode': args.preprocess_mode,
    }
    reply_json_path.write_text(json.dumps(reply_payload, ensure_ascii=False, indent=2), encoding='utf-8')
    safe_print(f'ROUNTRIP_REPLY_JSON={reply_json_path}')
    safe_print(f'ROUNTRIP_STT_TEXT_B64={reply_payload["stt_text_b64"]}')
    safe_print(f'ROUNTRIP_REPLY_TEXT_B64={reply_payload["reply_text_b64"]}')

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
