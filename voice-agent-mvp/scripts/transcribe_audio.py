def main():
    import argparse
    import json
    import subprocess
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description='Transcribe wav to text with the tmall local whisper path')
    parser.add_argument('wav_path', help='Path to wav file')
    parser.add_argument('--timeout-seconds', type=int, default=12)
    parser.add_argument('--culture', default='zh-CN')
    parser.add_argument('--engine', default='local_whisper', choices=['local_whisper', 'system_speech'])
    parser.add_argument('--whisper-model', default='small')
    parser.add_argument('--preprocess-mode', default='standard', choices=['standard', 'wake'])
    parser.add_argument('--result-json', default=str(Path(__file__).resolve().parents[1] / 'output' / 'last_stt_result.json'))
    args = parser.parse_args()

    wav_path = Path(args.wav_path).resolve()
    if not wav_path.is_file():
        print(f'WAV_NOT_FOUND {wav_path}')
        raise SystemExit(1)

    helper = Path(__file__).resolve().parents[2] / 'skills' / 'tmall-genie-voice-bridge' / 'scripts' / 'listen_once.py'
    if not helper.is_file():
        print(f'STT_HELPER_NOT_FOUND {helper}')
        raise SystemExit(1)

    result_json_path = Path(args.result_json).resolve()

    cmd = [
        sys.executable,
        str(helper),
        '--wav',
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
    completed = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')

    def safe_write(text: str, *, is_error: bool = False) -> None:
        if not text:
            return
        stream = sys.stderr if is_error else sys.stdout
        payload = text.rstrip() + '\n'
        try:
            stream.write(payload)
        except UnicodeEncodeError:
            encoding = getattr(stream, 'encoding', None) or 'utf-8'
            repaired = payload.encode(encoding, errors='replace').decode(encoding, errors='replace')
            stream.write(repaired)
        stream.flush()

    if completed.stdout:
        safe_write(completed.stdout)
    if completed.stderr:
        safe_write(completed.stderr, is_error=True)

    if result_json_path.is_file():
        try:
            payload = json.loads(result_json_path.read_text(encoding='utf-8'))
            text = str(payload.get('text') or '').strip()
            text_b64 = str(payload.get('text_b64') or '').strip()
            safe_write(f'STT_RESULT_JSON={result_json_path}')
            if text:
                safe_write(f'STT_TEXT_FILE={text}')
            if text_b64:
                safe_write(f'STT_TEXT_B64={text_b64}')
        except Exception as exc:
            safe_write(f'STT_RESULT_JSON_READ_ERROR={exc}', is_error=True)

    raise SystemExit(completed.returncode)


if __name__ == '__main__':
    main()
