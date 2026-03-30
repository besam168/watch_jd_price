from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from speak import load_config, speak


def _powershell_recognize(*, timeout_seconds: int, culture: str, wav_path: Path | None) -> Dict[str, Any]:
    payload = {
        "timeout_seconds": int(timeout_seconds),
        "culture": culture,
        "wav_path": str(wav_path) if wav_path else "",
    }
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")

    script = rf'''
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech

$PayloadBase64 = '{encoded}'
$payloadJson = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($PayloadBase64))
$payload = $payloadJson | ConvertFrom-Json
$timeoutSeconds = [int]$payload.timeout_seconds
$culture = [string]$payload.culture
$wavPath = [string]$payload.wav_path

$result = [ordered]@{{
  ok = $false
  mode = if ([string]::IsNullOrWhiteSpace($wavPath)) {{ 'microphone' }} else {{ 'wav_file' }}
  text = ''
  confidence = $null
  culture = $culture
  timed_out = $false
  wav_path = if ([string]::IsNullOrWhiteSpace($wavPath)) {{ $null }} else {{ $wavPath }}
  error = $null
}}

try {{
  $recognizerInfo = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() |
    Where-Object {{ $_.Culture.Name -eq $culture }} |
    Select-Object -First 1

  if (-not $recognizerInfo) {{
    $installed = [System.Speech.Recognition.SpeechRecognitionEngine]::InstalledRecognizers() |
      ForEach-Object {{ $_.Culture.Name }}
    throw ("No recognizer installed for culture '{0}'. Installed: {1}" -f $culture, ($installed -join ', '))
  }}

  $engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($recognizerInfo)
  $engine.LoadGrammar([System.Speech.Recognition.DictationGrammar]::new())

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
      $result.culture = $culture
    }}
  }}

  $engine.Dispose()
}}
catch {{
  $result.error = $_.Exception.Message
}}

$result | ConvertTo-Json -Depth 4 -Compress
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
    if not stdout:
        raise RuntimeError("PowerShell recognition returned no output")

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse recognition output: {stdout}") from exc


def listen_once(*, timeout_seconds: int, culture: str, wav_path: Path | None) -> Dict[str, Any]:
    result = _powershell_recognize(timeout_seconds=timeout_seconds, culture=culture, wav_path=wav_path)
    result.setdefault("ok", False)
    result.setdefault("text", "")
    result.setdefault("culture", culture)
    result.setdefault("mode", "wav_file" if wav_path else "microphone")
    if wav_path and not result.get("wav_path"):
        result["wav_path"] = str(wav_path)
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
        default=6,
        help="Recognition timeout in seconds for either microphone or wav recognition.",
    )
    parser.add_argument(
        "--culture",
        default="zh-CN",
        help="Recognizer culture, default zh-CN.",
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

    try:
        result = listen_once(
            timeout_seconds=args.timeout_seconds,
            culture=args.culture,
            wav_path=wav_path,
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
        print(json.dumps(error, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
