from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict
from urllib.parse import urlsplit, urlunsplit
from uuid import uuid4

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from backends.local_http_player import LocalHttpPlayerBackend
from backends.local_windows_speaker import LocalWindowsSpeakerBackend
from backends.mock_tmall_genie import MockTmallGenieBackend
from providers.tts_edge import synthesize_sync as edge_synthesize_sync
from providers.tts_mock import synthesize_sync as mock_synthesize_sync


BACKENDS = {
    "mock_tmall_genie": MockTmallGenieBackend,
    "local_http_player": LocalHttpPlayerBackend,
    "local_windows_speaker": LocalWindowsSpeakerBackend,
}

PROVIDERS: Dict[str, Dict[str, Any]] = {
    "edge": {
        "synthesize": edge_synthesize_sync,
        "default_extension": "mp3",
    },
    "mock": {
        "synthesize": mock_synthesize_sync,
        "default_extension": "wav",
    },
}


def normalize_text(text: str, *, config: Dict[str, Any]) -> str:
    normalized = str(text).strip()
    if not normalized:
        raise ValueError("Input text is empty after trimming")

    max_text_length = int((config.get("tts") or {}).get("max_text_length", 4000))
    if max_text_length > 0 and len(normalized) > max_text_length:
        raise ValueError(f"Input text is too long ({len(normalized)} > {max_text_length})")
    return normalized


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8-sig"))


def build_audio_url(config: Dict[str, Any], audio_file: Path) -> str | None:
    http_player = config.get("http_player") or {}

    public_base_url = str(http_player.get("public_base_url") or "").strip()
    if public_base_url:
        return join_audio_base_url(public_base_url.rstrip("/") + "/audio", audio_file.name)

    audio_base_url = http_player.get("audio_base_url")
    if not audio_base_url:
        return None
    if str(audio_base_url).strip().lower() == "auto":
        return None
    return join_audio_base_url(str(audio_base_url), audio_file.name)


def join_audio_base_url(audio_base_url: str, filename: str) -> str:
    normalized = str(audio_base_url).rstrip("/")
    if not normalized:
        raise ValueError("audio_base_url cannot be empty")

    parsed = urlsplit(normalized)
    path = parsed.path.rstrip("/") + "/" + filename
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def resolve_output_dir(config: Dict[str, Any], config_path: Path) -> Path:
    tts = config.get("tts") or {}
    output_dir = Path(tts.get("output_dir", "./tmp_audio"))
    if not output_dir.is_absolute():
        output_dir = (config_path.parent / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def resolve_output_extension(config: Dict[str, Any], provider_name: str) -> str:
    provider_meta = PROVIDERS.get(provider_name)
    if not provider_meta:
        raise ValueError(f"Unsupported tts.provider: {provider_name}")

    configured = str((config.get("tts") or {}).get("output_ext", "")).strip().lower()
    if configured:
        return configured.lstrip(".")
    return str(provider_meta["default_extension"])


def synthesize_audio(*, text: str, config: Dict[str, Any], output_dir: Path) -> Path:
    tts = config.get("tts") or {}
    provider_name = str(tts.get("provider", "edge")).strip().lower()
    provider_meta = PROVIDERS.get(provider_name)
    if not provider_meta:
        supported = ", ".join(sorted(PROVIDERS.keys()))
        raise ValueError(f"Unsupported tts.provider: {provider_name}. Supported: {supported}")

    extension = resolve_output_extension(config, provider_name)
    filename = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8] + "." + extension
    audio_path = output_dir / filename

    synthesize_fn: Callable[..., Path] = provider_meta["synthesize"]
    synthesize_fn(
        text=text,
        output_path=audio_path,
        voice=tts.get("voice", "zh-CN-XiaoxiaoNeural"),
        rate=tts.get("rate", "+0%"),
    )
    return audio_path


def build_backend_options(backend_type: str, config: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    backend_cfg = config.get("backend") or {}
    backend_options = dict(backend_cfg.get("options") or {})

    if backend_type == "local_http_player":
        backend_options.update(config.get("http_player") or {})

    if backend_type == "local_windows_speaker":
        backend_options.update(config.get("local_windows_speaker") or {})
        backend_options["config_dir"] = str(config_path.parent)
        backend_options["skill_dir"] = str(Path(__file__).resolve().parents[1])

    return backend_options


def speak(
    *,
    text: str,
    config: Dict[str, Any],
    config_path: Path,
    audio_base_url_override: str | None = None,
) -> Dict[str, Any]:
    normalized_text = normalize_text(text=text, config=config)
    backend_cfg = config.get("backend") or {}
    backend_type = backend_cfg.get("type", "mock_tmall_genie")
    backend_options = build_backend_options(backend_type, config, config_path)

    backend_cls = BACKENDS.get(backend_type)
    if not backend_cls:
        supported = ", ".join(sorted(BACKENDS.keys()))
        raise ValueError(f"Unsupported backend.type: {backend_type}. Supported: {supported}")

    output_dir = resolve_output_dir(config, config_path)
    audio_path = synthesize_audio(text=normalized_text, config=config, output_dir=output_dir)

    audio_url = (
        join_audio_base_url(audio_base_url_override, audio_path.name)
        if audio_base_url_override
        else build_audio_url(config, audio_path)
    )
    backend = backend_cls(backend_options)
    backend_result = backend.play(text=normalized_text, audio_path=audio_path, audio_url=audio_url)

    return {
        "ok": True,
        "text": normalized_text,
        "audio_path": str(audio_path),
        "audio_url": audio_url,
        "backend": backend_type,
        "backend_result": backend_result,
    }


def main() -> None:
    # 设置控制台输出编码为UTF-8，解决中文乱码问题
    if sys.platform == "win32":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description="Generate audio from text and dispatch playback through the configured backend."
    )
    parser.add_argument("text", help="Text to speak")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.json"),
        help="Path to config JSON file",
    )
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    try:
        result = speak(text=args.text, config=config, config_path=config_path)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:
        error = {"ok": False, "error": str(exc)}
        print(json.dumps(error, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
