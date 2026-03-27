from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from backends.local_http_player import LocalHttpPlayerBackend
from backends.mock_tmall_genie import MockTmallGenieBackend
from providers.tts_edge import synthesize_sync


BACKENDS = {
    "mock_tmall_genie": MockTmallGenieBackend,
    "local_http_player": LocalHttpPlayerBackend,
}


def load_config(config_path: Path) -> Dict[str, Any]:
    return json.loads(config_path.read_text(encoding="utf-8"))


def build_audio_url(config: Dict[str, Any], audio_file: Path) -> str | None:
    http_player = config.get("http_player") or {}
    audio_base_url = http_player.get("audio_base_url")
    if not audio_base_url:
        return None
    return audio_base_url.rstrip("/") + "/" + audio_file.name


def speak(*, text: str, config: Dict[str, Any], config_path: Path) -> Dict[str, Any]:
    tts = config.get("tts") or {}
    backend_cfg = config.get("backend") or {}
    backend_type = backend_cfg.get("type", "mock_tmall_genie")
    backend_options = dict(backend_cfg.get("options") or {})

    if backend_type == "local_http_player":
        backend_options.update(config.get("http_player") or {})

    backend_cls = BACKENDS.get(backend_type)
    if not backend_cls:
        raise ValueError(f"不支持的 backend.type: {backend_type}")

    output_dir = Path(tts.get("output_dir", "./tmp_audio"))
    if not output_dir.is_absolute():
        output_dir = (config_path.parent / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid4().hex[:8] + ".mp3"
    audio_path = output_dir / filename

    provider = tts.get("provider", "edge")
    if provider != "edge":
        raise ValueError(f"当前只支持 tts.provider=edge，实际收到: {provider}")

    synthesize_sync(
        text=text,
        output_path=audio_path,
        voice=tts.get("voice", "zh-CN-XiaoxiaoNeural"),
        rate=tts.get("rate", "+0%"),
    )

    audio_url = build_audio_url(config, audio_path)
    backend = backend_cls(backend_options)
    backend_result = backend.play(text=text, audio_path=audio_path, audio_url=audio_url)

    return {
        "ok": True,
        "text": text,
        "audio_path": str(audio_path),
        "audio_url": audio_url,
        "backend": backend_type,
        "backend_result": backend_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="天猫精灵语音桥：文本转语音并触发播放后端")
    parser.add_argument("text", help="要播报的文本")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"), help="配置文件路径")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    result = speak(text=args.text, config=config, config_path=config_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
