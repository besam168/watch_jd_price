from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from speak import load_config, speak


SYSTEM_SPEECH_NOTE = (
    "Windows System.Speech dictation is best-effort. "
    "zh-CN recognition quality and timeout behavior can vary by device, room noise, and installed language packs."
)

LOCAL_WHISPER_NOTE = (
    "Local Whisper runs offline after model download and is currently the preferred path for Chinese wav transcription on this machine."
)

SKILL_ROOT = CURRENT_DIR.parent
WORKSPACE_ROOT = SKILL_ROOT.parent.parent
LOCAL_WHISPER_ROOT = WORKSPACE_ROOT / "skills" / "local-whisper"
LOCAL_WHISPER_VENV_PYTHON = LOCAL_WHISPER_ROOT / ".venv" / "Scripts" / "python.exe"
LOCAL_WHISPER_FFMPEG = LOCAL_WHISPER_ROOT / ".venv" / "Scripts" / "ffmpeg.exe"


def _resolve_local_whisper_env() -> tuple[dict[str, str], str]:
    env = os.environ.copy()
    ffmpeg_dir = str(LOCAL_WHISPER_FFMPEG.parent)
    env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")
    env["PYTHONIOENCODING"] = "utf-8"

    ffmpeg_named = shutil.which("ffmpeg", path=env["PATH"])
    if not ffmpeg_named:
        raise RuntimeError(
            f"ffmpeg executable not found in PATH for Local Whisper. Expected under: {LOCAL_WHISPER_FFMPEG.parent}"
        )

    return env, ffmpeg_named


def _record_microphone_to_wav(*, timeout_seconds: int, mic_device: str | None) -> tuple[Path, str]:
    env, ffmpeg_named = _resolve_local_whisper_env()

    with tempfile.NamedTemporaryFile(prefix="tmall-mic-", suffix=".wav", delete=False) as tmp:
        wav_path = Path(tmp.name)

    device_name = str(mic_device or "").strip() or "audio=麦克风 (Logi C270 HD WebCam)"
    if not device_name.lower().startswith("audio="):
        device_name = f"audio={device_name}"

    command = [
        ffmpeg_named,
        "-y",
        "-f",
        "dshow",
        "-i",
        device_name,
        "-t",
        str(int(timeout_seconds)),
        "-ac",
        "1",
        "-ar",
        "16000",
        str(wav_path),
    ]

    started_at = time.time()
    completed = subprocess.run(command, capture_output=True, text=False, check=False, env=env)
    elapsed_ms = int((time.time() - started_at) * 1000)
    stdout = (completed.stdout or b"").decode("utf-8", errors="ignore").strip()
    stderr = (completed.stderr or b"").decode("utf-8", errors="ignore").strip()

    if completed.returncode != 0:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError(stderr or stdout or f"ffmpeg microphone capture failed with exit code {completed.returncode}")

    if not wav_path.is_file() or wav_path.stat().st_size <= 44:
        try:
            wav_path.unlink(missing_ok=True)
        except Exception:
            pass
        raise RuntimeError("ffmpeg microphone capture produced an empty wav file")

    return wav_path, device_name


def _run_local_whisper(*, wav_path: Path, language: str, model: str) -> Dict[str, Any]:
    if not wav_path or not wav_path.is_file():
        raise RuntimeError("Local Whisper requires an existing --wav file")

    if not LOCAL_WHISPER_VENV_PYTHON.is_file():
        raise RuntimeError(f"Local Whisper venv python not found: {LOCAL_WHISPER_VENV_PYTHON}")

    env, ffmpeg_named = _resolve_local_whisper_env()

    command = [
        str(LOCAL_WHISPER_VENV_PYTHON),
        "-c",
        (
            "import json, whisper; "
            f"m=whisper.load_model({json.dumps(model)}); "
            f"r=m.transcribe(r'{str(wav_path)}', language={json.dumps(language)}, verbose=False); "
            "print(json.dumps({'text': r['text'].strip(), 'language': r.get('language', 'unknown')}, ensure_ascii=False))"
        ),
    ]

    completed = subprocess.run(command, capture_output=True, text=False, check=False, env=env)
    stdout = (completed.stdout or b"").decode("utf-8", errors="ignore").strip()
    stderr = (completed.stderr or b"").decode("utf-8", errors="ignore").strip()

    if completed.returncode != 0:
        raise RuntimeError(stderr or stdout or f"Local Whisper failed with exit code {completed.returncode}")
    if not stdout:
        raise RuntimeError("Local Whisper returned no output")

    json_lines = [line.strip() for line in stdout.splitlines() if line.strip().startswith("{")]
    payload = json.loads(json_lines[-1] if json_lines else stdout.splitlines()[-1])
    text = str(payload.get("text") or "").strip()

    return {
        "ok": bool(text),
        "mode": "wav_file",
        "text": text,
        "confidence": None,
        "culture": str(payload.get("language") or language or "unknown"),
        "requested_culture": language,
        "selected_culture": str(payload.get("language") or language or "unknown"),
        "culture_fallback_used": False,
        "installed_recognizers": [],
        "timed_out": False,
        "wav_path": str(wav_path),
        "elapsed_ms": 0,
        "error": None if text else "Local Whisper returned empty text",
        "engine": {
            "name": "local_whisper",
            "transport": "python_subprocess",
            "model": model,
            "note": LOCAL_WHISPER_NOTE,
            "ffmpeg": ffmpeg_named,
            "python": str(LOCAL_WHISPER_VENV_PYTHON),
        },
    }


def _decode_powershell_json(stdout: str) -> Dict[str, Any]:
    lines = [line.strip() for line in stdout.splitlines() if line.strip()]
    if not lines:
        raise RuntimeError("PowerShell recognition returned no output")

    last_line = lines[-1]
    try:
        decoded = base64.b64decode(last_line, validate=True)
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        pass

    try:
        return json.loads(last_line)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse recognition output: {stdout}") from exc


def _powershell_recognize(
    *,
    timeout_seconds: int,
    culture: str,
    wav_path: Path | None,
    initial_silence_seconds: float,
    babble_timeout_seconds: float,
    end_silence_seconds: float,
    allow_culture_fallback: bool,
) -> Dict[str, Any]:
    payload = {
        "timeout_seconds": int(timeout_seconds),
        "culture": culture,
        "wav_path": str(wav_path) if wav_path else "",
        "initial_silence_seconds": float(initial_silence_seconds),
        "babble_timeout_seconds": float(babble_timeout_seconds),
        "end_silence_seconds": float(end_silence_seconds),
        "allow_culture_fallback": bool(allow_culture_fallback),
    }
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

    script = rf'''
$ErrorActionPreference = 'Stop'
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Speech

$PayloadBase64 = '{encoded}'
$payloadJson = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($PayloadBase64))
$payload = $payloadJson | ConvertFrom-Json
$timeoutSeconds = [int]$payload.timeout_seconds
$culture = [string]$payload.culture
$wavPath = [string]$payload.wav_path
$initialSilenceSeconds = [double]$payload.initial_silence_seconds
$babbleTimeoutSeconds = [double]$payload.babble_timeout_seconds
$endSilenceSeconds = [double]$payload.end_silence_seconds
$allowCultureFallback = [bool]$payload.allow_culture_fallback

$result = [ordered]@{{
  ok = $false
  mode = if ([string]::IsNullOrWhiteSpace($wavPath)) {{ 'microphone' }} else {{ 'wav_file' }}
  text = ''
  confidence = $null
  culture = $culture
  requested_culture = $culture
  selected_culture = $null
  culture_fallback_used = $false
  installed_recognizers = @()
  timed_out = $false
  wav_path = if ([string]::IsNullOrWhiteSpace($wavPath)) {{ $null }} else {{ $wavPath }}
  elapsed_ms = 0
  error = $null
}}

$sw = [System.Diagnostics.Stopwatch]::StartNew()

try {{
  $installedRecognizers = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers()
  $result.installed_recognizers = @($installedRecognizers | ForEach-Object {{ $_.Culture.Name }})

  if (-not $installedRecognizers -or $installedRecognizers.Count -eq 0) {{
    throw 'No System.Speech recognizers are installed on this machine.'
  }}

  $recognizerInfo = $installedRecognizers | Where-Object {{ $_.Culture.Name -eq $culture }} | Select-Object -First 1

  if (-not $recognizerInfo) {{
    if ($allowCultureFallback) {{
      $recognizerInfo = $installedRecognizers | Select-Object -First 1
      $result.culture_fallback_used = $true
    }}
    else {{
      throw ("No recognizer installed for culture '{0}'. Installed: {1}" -f $culture, ($result.installed_recognizers -join ', '))
    }}
  }}

  $result.selected_culture = $recognizerInfo.Culture.Name
  $engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($recognizerInfo)
  $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())
  $engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds($initialSilenceSeconds)
  $engine.BabbleTimeout = [TimeSpan]::FromSeconds($babbleTimeoutSeconds)
  $engine.EndSilenceTimeout = [TimeSpan]::FromSeconds($endSilenceSeconds)

  if ([string]::IsNullOrWhiteSpace($wavPath)) {{
    $engine.SetInputToDefaultAudioDevice()
  }}
  else {{
    $resolved = (Resolve-Path -LiteralPath $wavPath).Path
    $engine.SetInputToWaveFile($resolved)
    $result.wav_path = $resolved
  }}

  $recognized = $engine.Recognize([TimeSpan]::FromSeconds($timeoutSeconds))

  if ($null -eq $recognized) {{
    $result.timed_out = $true
    $result.error = 'No speech recognized before timeout.'
  }}
  else {{
    $result.ok = $true
    $result.text = $recognized.Text
    $result.confidence = [double]$recognized.Confidence
    if ($recognized.Grammar -and $recognized.Grammar.Culture) {{
      $result.culture = $recognized.Grammar.Culture.Name
    }}
    else {{
      $result.culture = $result.selected_culture
    }}
  }}

  $engine.Dispose()
}}
catch {{
  $result.error = $_.Exception.Message
}}
finally {{
  $sw.Stop()
  $result.elapsed_ms = [int]$sw.ElapsedMilliseconds
}}

$json = $result | ConvertTo-Json -Depth 6 -Compress
[Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($json))
'''

    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        script,
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    stdout = (completed.stdout or "").strip()
    stderr = (completed.stderr or "").strip()

    if completed.returncode != 0:
        raise RuntimeError(stderr or stdout or f"PowerShell recognition failed with exit code {completed.returncode}")
    if not stdout.strip():
        raise RuntimeError("PowerShell recognition returned no output")

    return _decode_powershell_json(stdout)


def _choose_best_attempt(attempts: List[Dict[str, Any]]) -> Dict[str, Any]:
    successful = [item for item in attempts if item.get("ok") and str(item.get("text") or "").strip()]
    if successful:
        return max(successful, key=lambda item: float(item.get("confidence") or 0.0))

    partially_successful = [item for item in attempts if item.get("ok")]
    if partially_successful:
        return partially_successful[0]

    return attempts[-1]


def _build_warnings(
    *,
    result: Dict[str, Any],
    timeout_seconds: int,
    primary_mode: str,
    fallback_wav: Path | None,
) -> List[str]:
    warnings: List[str] = []
    warnings.append(SYSTEM_SPEECH_NOTE)

    attempt_items = result.get("attempts") if isinstance(result.get("attempts"), list) else []
    primary_attempts = [item for item in attempt_items if isinstance(item, dict)]
    timeout_seen = bool(result.get("timed_out")) or any(item.get("timed_out") for item in primary_attempts)
    primary_success_seen = bool(result.get("ok")) and result.get("result_source") == "primary"
    culture_fallback_seen = bool(result.get("culture_fallback_used")) or any(
        item.get("culture_fallback_used") for item in primary_attempts
    )

    if culture_fallback_seen:
        selected = result.get("selected_culture")
        requested = result.get("requested_culture")
        if not selected or not requested:
            for item in primary_attempts:
                selected = selected or item.get("selected_culture")
                requested = requested or item.get("requested_culture")
        selected = str(selected or "unknown")
        requested = str(requested or "unknown")
        warnings.append(
            f"Requested culture '{requested}' was not installed. Recognition fell back to '{selected}'."
        )

    if primary_mode == "microphone" and timeout_seen:
        warnings.append(
            f"Microphone timed out after {timeout_seconds}s. Try a higher timeout or reduce room noise."
        )

    if primary_mode == "microphone" and not primary_success_seen:
        warnings.append("If microphone recognition is unstable, validate STT with the deterministic --wav path first.")

    if fallback_wav and result.get("result_source") == "fallback_wav":
        warnings.append("Microphone recognition failed; output text came from --fallback-wav.")
    elif fallback_wav and isinstance(result.get("fallback"), dict):
        fallback_error = str(result["fallback"].get("error") or "").strip()
        if fallback_error:
            warnings.append(f"Fallback WAV attempt failed: {fallback_error}")
        else:
            warnings.append("Fallback WAV attempt failed.")

    return warnings


def _run_recognition_attempts(
    *,
    timeout_seconds: int,
    culture: str,
    wav_path: Path | None,
    attempts: int,
    initial_silence_seconds: float,
    babble_timeout_seconds: float,
    end_silence_seconds: float,
    allow_culture_fallback: bool,
) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for attempt_index in range(1, attempts + 1):
        current = _powershell_recognize(
            timeout_seconds=timeout_seconds,
            culture=culture,
            wav_path=wav_path,
            initial_silence_seconds=initial_silence_seconds,
            babble_timeout_seconds=babble_timeout_seconds,
            end_silence_seconds=end_silence_seconds,
            allow_culture_fallback=allow_culture_fallback,
        )
        current["attempt"] = attempt_index
        results.append(current)
        if current.get("ok") and str(current.get("text") or "").strip():
            break
    return results


def listen_once(
    *,
    timeout_seconds: int,
    culture: str,
    wav_path: Path | None,
    attempts: int,
    fallback_wav: Path | None,
    initial_silence_seconds: float,
    babble_timeout_seconds: float,
    end_silence_seconds: float,
    allow_culture_fallback: bool,
    engine: str,
    whisper_model: str,
    mic_device: str | None,
) -> Dict[str, Any]:
    primary_mode = "wav_file" if wav_path else "microphone"

    if engine == "local_whisper":
        cleanup_wav: Path | None = None
        recorded_device: str | None = None
        try:
            actual_wav_path = wav_path
            if not actual_wav_path:
                cleanup_wav, recorded_device = _record_microphone_to_wav(
                    timeout_seconds=timeout_seconds,
                    mic_device=mic_device,
                )
                actual_wav_path = cleanup_wav

            result = _run_local_whisper(
                wav_path=actual_wav_path,
                language=culture.split("-")[0].lower(),
                model=whisper_model,
            )
            result.setdefault("ok", False)
            result.setdefault("text", "")
            result.setdefault("culture", culture)
            result.setdefault("mode", primary_mode)
            result["result_source"] = "primary"
            result["attempt_count"] = 1
            if cleanup_wav:
                result["recorded_wav_path"] = str(cleanup_wav)
            if recorded_device:
                result["mic_device"] = recorded_device
                result["mode"] = "microphone"
            result["warnings"] = [LOCAL_WHISPER_NOTE]
            return result
        finally:
            if cleanup_wav:
                try:
                    cleanup_wav.unlink(missing_ok=True)
                except Exception:
                    pass

    attempt_count = 1 if wav_path else max(1, int(attempts))

    attempt_results = _run_recognition_attempts(
        timeout_seconds=timeout_seconds,
        culture=culture,
        wav_path=wav_path,
        attempts=attempt_count,
        initial_silence_seconds=initial_silence_seconds,
        babble_timeout_seconds=babble_timeout_seconds,
        end_silence_seconds=end_silence_seconds,
        allow_culture_fallback=allow_culture_fallback,
    )
    result = dict(_choose_best_attempt(attempt_results))
    result.setdefault("ok", False)
    result.setdefault("text", "")
    result.setdefault("culture", culture)
    result.setdefault("mode", primary_mode)
    result["result_source"] = "primary"
    result["engine"] = {
        "name": "windows_system_speech",
        "transport": "powershell",
        "note": SYSTEM_SPEECH_NOTE,
    }
    if len(attempt_results) > 1:
        result["attempts"] = attempt_results
    result["attempt_count"] = len(attempt_results)

    if wav_path and not result.get("wav_path"):
        result["wav_path"] = str(wav_path)

    fallback_result: Dict[str, Any] | None = None
    if fallback_wav and not wav_path and not result.get("ok"):
        fallback_result = _powershell_recognize(
            timeout_seconds=timeout_seconds,
            culture=culture,
            wav_path=fallback_wav,
            initial_silence_seconds=initial_silence_seconds,
            babble_timeout_seconds=babble_timeout_seconds,
            end_silence_seconds=end_silence_seconds,
            allow_culture_fallback=allow_culture_fallback,
        )
        fallback_result["attempt"] = 1
        result["fallback"] = fallback_result
        if fallback_result.get("ok") and str(fallback_result.get("text") or "").strip():
            result["ok"] = True
            result["text"] = str(fallback_result["text"])
            result["confidence"] = fallback_result.get("confidence")
            result["culture"] = str(fallback_result.get("culture") or culture)
            result["wav_path"] = str(fallback_result.get("wav_path") or fallback_wav)
            result["result_source"] = "fallback_wav"

    result["warnings"] = _build_warnings(
        result=result,
        timeout_seconds=timeout_seconds,
        primary_mode=primary_mode,
        fallback_wav=fallback_wav,
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-shot speech input for tmall-genie-voice-bridge using Windows System.Speech."
    )
    parser.add_argument(
        "--wav",
        help="Optional WAV file path. If provided, transcribe this file instead of listening to the microphone.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=8,
        help="Recognition timeout in seconds for either microphone or wav recognition.",
    )
    parser.add_argument(
        "--attempts",
        type=int,
        default=2,
        help="Microphone retry attempts before failing. Ignored when --wav is provided.",
    )
    parser.add_argument(
        "--culture",
        default="zh-CN",
        help="Recognizer culture, default zh-CN.",
    )
    parser.add_argument(
        "--allow-culture-fallback",
        action="store_true",
        help="If requested culture is unavailable, fall back to the first installed recognizer culture.",
    )
    parser.add_argument(
        "--initial-silence-seconds",
        type=float,
        default=3.0,
        help="Initial silence timeout for System.Speech before speech starts.",
    )
    parser.add_argument(
        "--babble-timeout-seconds",
        type=float,
        default=2.0,
        help="Babble timeout for System.Speech.",
    )
    parser.add_argument(
        "--end-silence-seconds",
        type=float,
        default=0.8,
        help="End-of-speech silence timeout for System.Speech.",
    )
    parser.add_argument(
        "--fallback-wav",
        help="Optional WAV file used only when microphone recognition fails. Useful as a practical fallback path.",
    )
    parser.add_argument(
        "--engine",
        choices=["system_speech", "local_whisper"],
        default="system_speech",
        help="Speech recognition engine. local_whisper currently supports --wav mode and is preferred for Chinese wav transcription.",
    )
    parser.add_argument(
        "--whisper-model",
        default="base",
        help="Whisper model name when --engine local_whisper is selected.",
    )
    parser.add_argument(
        "--mic-device",
        help="Optional ffmpeg dshow audio device name for microphone capture. Example: '麦克风 (Logi C270 HD WebCam)'.",
    )
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.local-speaker.json"),
        help="Config JSON used when --echo-speak is enabled.",
    )
    parser.add_argument(
        "--echo-speak",
        action="store_true",
        help="If recognition succeeds, hand recognized text to scripts/speak.py flow.",
    )
    args = parser.parse_args()

    wav_path = Path(args.wav).resolve() if args.wav else None
    fallback_wav = Path(args.fallback_wav).resolve() if args.fallback_wav else None

    if wav_path and fallback_wav:
        parser.error("--fallback-wav cannot be used together with --wav")
    if wav_path and not wav_path.is_file():
        parser.error(f"--wav file does not exist: {wav_path}")
    if fallback_wav and not fallback_wav.is_file():
        parser.error(f"--fallback-wav file does not exist: {fallback_wav}")
    if args.attempts < 1:
        parser.error("--attempts must be >= 1")
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be >= 1")
    if args.initial_silence_seconds <= 0 or args.babble_timeout_seconds <= 0 or args.end_silence_seconds <= 0:
        parser.error("silence timeout arguments must be > 0")

    try:
        result = listen_once(
            timeout_seconds=args.timeout_seconds,
            culture=args.culture,
            wav_path=wav_path,
            attempts=args.attempts,
            fallback_wav=fallback_wav,
            initial_silence_seconds=args.initial_silence_seconds,
            babble_timeout_seconds=args.babble_timeout_seconds,
            end_silence_seconds=args.end_silence_seconds,
            allow_culture_fallback=bool(args.allow_culture_fallback),
            engine=args.engine,
            whisper_model=args.whisper_model,
            mic_device=args.mic_device,
        )

        if args.echo_speak and result.get("ok") and result.get("text"):
            config_path = Path(args.config).resolve()
            config = load_config(config_path)
            result["speak_result"] = speak(
                text=str(result["text"]),
                config=config,
                config_path=config_path,
            )

        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result.get("ok") else 1)
    except Exception as exc:
        error = {
            "ok": False,
            "text": "",
            "error": str(exc),
            "mode": "wav_file" if wav_path else "microphone",
            "culture": args.culture,
        }
        if wav_path:
            error["wav_path"] = str(wav_path)
        if fallback_wav:
            error["fallback_wav"] = str(fallback_wav)
        error["warnings"] = [SYSTEM_SPEECH_NOTE]
        print(json.dumps(error, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
