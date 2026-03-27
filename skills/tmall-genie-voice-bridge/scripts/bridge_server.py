from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from flask import Flask, jsonify, request, send_from_directory

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from speak import load_config, speak


app = Flask(__name__)
APP_CONFIG: Dict[str, Any] = {}
APP_CONFIG_PATH: Path | None = None


@app.get("/health")
def health() -> Any:
    return jsonify({
        "ok": True,
        "service": "tmall-genie-voice-bridge",
        "backend": ((APP_CONFIG.get("backend") or {}).get("type") if APP_CONFIG else None),
    })


@app.post("/speak")
def speak_route() -> Any:
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "error": "缺少 text"}), 400

    result = speak(text=text, config=APP_CONFIG, config_path=APP_CONFIG_PATH)
    return jsonify(result)


@app.get("/audio/<path:filename>")
def audio_file(filename: str) -> Any:
    tts = APP_CONFIG.get("tts") or {}
    output_dir = Path(tts.get("output_dir", "./tmp_audio"))
    if not output_dir.is_absolute():
        output_dir = (APP_CONFIG_PATH.parent / output_dir).resolve()
    return send_from_directory(output_dir, filename)


def main() -> None:
    global APP_CONFIG, APP_CONFIG_PATH

    parser = argparse.ArgumentParser(description="天猫精灵语音桥本地 HTTP 服务")
    parser.add_argument("--config", default=str(Path(__file__).resolve().parents[1] / "config.json"), help="配置文件路径")
    args = parser.parse_args()

    APP_CONFIG_PATH = Path(args.config).resolve()
    APP_CONFIG = load_config(APP_CONFIG_PATH)

    host = APP_CONFIG.get("host", "127.0.0.1")
    port = int(APP_CONFIG.get("port", 57881))
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
