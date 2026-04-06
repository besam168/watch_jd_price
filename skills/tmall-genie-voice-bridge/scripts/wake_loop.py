from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from listen_once import DEFAULT_MIC_DEVICE, listen_once
from speak import load_config, speak

FAST_WAKE_TIMEOUT_SECONDS = 3
FAST_WAKE_PRE_ROLL_SECONDS = 0.2
FAST_WAKE_COOLDOWN_SECONDS = 0.3


def normalize_text(value: str) -> str:
    normalized = str(value or "").strip().lower()
    normalized = re.sub(r"\s+", "", normalized)
    normalized = re.sub(r"[\W_]+", "", normalized)
    return normalized


def build_wake_variants(wake_phrase: str) -> set[str]:
    base = normalize_text(wake_phrase)
    variants = {
        base,
        "啊三在吗",
        "阿三在吗",
        "阿山在吗",
        "啊山在吗",
        "阿三在么",
        "啊三在么",
        "阿山在么",
        "啊山在么",
        "啊三",
        "阿三",
        "阿3",
        "a3",
        "a三",
        "啊3",
        "呀三",
        "亚三",
        "阿叁",
        "阿山",
        "啊山",
        "阿杉",
        "啊杉",
        "阿散",
        "啊散",
        "啊三啊",
        "阿三啊",
    }
    return {normalize_text(v) for v in variants if normalize_text(v)}


def contains_wake_phrase(recognized_text: str, wake_phrase: str) -> bool:
    recognized = normalize_text(recognized_text)
    if not recognized:
        return False
    variants = build_wake_variants(wake_phrase)
    return any(variant and variant in recognized for variant in variants)


def run_loop(
    *,
    config_path: Path,
    culture: str,
    timeout_seconds: int,
    whisper_model: str,
    mic_device: str,
    wake_phrase: str,
    response_text: str,
    pre_roll_seconds: float,
    cooldown_seconds: float,
    keep_recorded_wav: bool,
    max_turns: int,
) -> int:
    config = load_config(config_path)
    trigger_count = 0

    print(
        json.dumps(
            {
                "ok": True,
                "status": "listening",
                "wake_phrase": wake_phrase,
                "response_text": response_text,
                "engine": "local_whisper",
                "model": whisper_model,
                "mic_device": mic_device,
                "timeout_seconds": timeout_seconds,
                "pre_roll_seconds": pre_roll_seconds,
                "cooldown_seconds": cooldown_seconds,
                "wake_variants": sorted(build_wake_variants(wake_phrase)),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    while True:
        result = listen_once(
            timeout_seconds=timeout_seconds,
            culture=culture,
            wav_path=None,
            attempts=1,
            fallback_wav=None,
            initial_silence_seconds=1.2,
            babble_timeout_seconds=1.0,
            end_silence_seconds=0.35,
            allow_culture_fallback=False,
            engine="local_whisper",
            whisper_model=whisper_model,
            mic_device=mic_device,
            keep_recorded_wav=keep_recorded_wav,
            pre_roll_seconds=pre_roll_seconds,
            preprocess_mode="wake",
        )

        recognized_text = str(result.get("text") or "").strip()
        triggered = bool(result.get("ok")) and contains_wake_phrase(recognized_text, wake_phrase)

        event: dict[str, Any] = {
            "ok": bool(result.get("ok")),
            "triggered": triggered,
            "recognized_text": recognized_text,
            "recorded_wav_path": result.get("recorded_wav_path"),
            "cleaned_wav_path": result.get("cleaned_wav_path"),
            "level_summary": result.get("level_summary"),
            "cleaned_level_summary": result.get("cleaned_level_summary"),
            "warnings": result.get("warnings") or [],
        }

        if not result.get("ok"):
            event["error"] = result.get("error")
            print(json.dumps(event, ensure_ascii=False), flush=True)
            continue

        if triggered:
            speak_result = speak(text=response_text, config=config, config_path=config_path)
            trigger_count += 1
            event["response_text"] = response_text
            event["speak_result"] = speak_result
            event["trigger_count"] = trigger_count
            print(json.dumps(event, ensure_ascii=False), flush=True)
            if max_turns > 0 and trigger_count >= max_turns:
                return 0
            if cooldown_seconds > 0:
                time.sleep(cooldown_seconds)
        else:
            print(json.dumps(event, ensure_ascii=False), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Continuously listen for a wake phrase and respond via local TTS.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.local-speaker.json"),
        help="Path to config JSON file",
    )
    parser.add_argument("--wake-phrase", default="啊三在吗", help="Wake phrase to detect")
    parser.add_argument("--response-text", default="我在", help="Text to speak when wake phrase is detected")
    parser.add_argument("--culture", default="zh-CN", help="Recognition culture/language hint")
    parser.add_argument("--timeout-seconds", type=int, default=FAST_WAKE_TIMEOUT_SECONDS, help="Per-listen capture duration in seconds")
    parser.add_argument("--whisper-model", default="small", help="Whisper model name")
    parser.add_argument("--mic-device", default=DEFAULT_MIC_DEVICE, help="ffmpeg dshow microphone device name")
    parser.add_argument("--pre-roll-seconds", type=float, default=FAST_WAKE_PRE_ROLL_SECONDS, help="Delay before each capture starts")
    parser.add_argument("--cooldown-seconds", type=float, default=FAST_WAKE_COOLDOWN_SECONDS, help="Delay after a successful wake response")
    parser.add_argument("--keep-recorded-wav", action="store_true", help="Keep captured wav files for debugging")
    parser.add_argument("--max-turns", type=int, default=1, help="Exit after this many successful wake detections; 0 means run forever")
    args = parser.parse_args()

    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be > 0")
    if args.pre_roll_seconds < 0:
        parser.error("--pre-roll-seconds must be >= 0")
    if args.cooldown_seconds < 0:
        parser.error("--cooldown-seconds must be >= 0")
    if args.max_turns < 0:
        parser.error("--max-turns must be >= 0")

    config_path = Path(args.config).resolve()
    raise SystemExit(
        run_loop(
            config_path=config_path,
            culture=args.culture,
            timeout_seconds=args.timeout_seconds,
            whisper_model=args.whisper_model,
            mic_device=args.mic_device,
            wake_phrase=args.wake_phrase,
            response_text=args.response_text,
            pre_roll_seconds=float(args.pre_roll_seconds),
            cooldown_seconds=float(args.cooldown_seconds),
            keep_recorded_wav=bool(args.keep_recorded_wav),
            max_turns=int(args.max_turns),
        )
    )


if __name__ == "__main__":
    main()
