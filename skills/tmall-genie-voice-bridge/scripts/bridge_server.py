from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, request, send_from_directory

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from speak import load_config, speak


app = Flask(__name__)
APP_CONFIG: Dict[str, Any] = {}
APP_CONFIG_PATH: Path | None = None


def _resolve_audio_base_url() -> str | None:
    http_player = APP_CONFIG.get("http_player") or {}
    configured = str(http_player.get("audio_base_url") or "").strip()
    public_base_url = str(http_player.get("public_base_url") or "").strip()

    if public_base_url:
        return public_base_url.rstrip("/") + "/audio"

    if not configured:
        return None

    lowered = configured.lower()
    if lowered == "auto":
        return request.url_root.rstrip("/") + "/audio"

    return configured


def _extract_text_callback_payload(data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    candidates = [
        data.get("text"),
        data.get("query"),
        data.get("utterance"),
        data.get("message"),
        (data.get("payload") or {}).get("text") if isinstance(data.get("payload"), dict) else None,
        (data.get("payload") or {}).get("query") if isinstance(data.get("payload"), dict) else None,
        (data.get("intent") or {}).get("query") if isinstance(data.get("intent"), dict) else None,
        (data.get("request") or {}).get("text") if isinstance(data.get("request"), dict) else None,
        (data.get("request") or {}).get("query") if isinstance(data.get("request"), dict) else None,
    ]

    text = ""
    for item in candidates:
        if item is None:
            continue
        value = str(item).strip()
        if value:
            text = value
            break

    metadata = {
        "source": str(data.get("source", "text_callback")).strip() or "text_callback",
        "session_id": str(data.get("session_id") or data.get("sessionId") or "").strip() or None,
        "user_id": str(data.get("user_id") or data.get("userId") or "").strip() or None,
        "trace_id": str(data.get("trace_id") or data.get("traceId") or "").strip() or None,
        "intent": data.get("intent") if isinstance(data.get("intent"), dict) else None,
    }
    return text, metadata


@app.get("/health")
def health() -> Any:
    backend_type = None
    if APP_CONFIG:
        backend_type = (APP_CONFIG.get("backend") or {}).get("type")
    return jsonify({
        "ok": True,
        "service": "tmall-genie-voice-bridge",
        "backend": backend_type,
    })


@app.post("/speak")
def speak_route() -> Any:
    data = request.get_json(silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"ok": False, "error": "Missing required field: text"}), 400

    try:
        result = speak(
            text=text,
            config=APP_CONFIG,
            config_path=APP_CONFIG_PATH,
            audio_base_url_override=_resolve_audio_base_url(),
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify(result)


@app.post("/callback/text")
@app.post("/webhook/text")
def text_callback_route() -> Any:
    data = request.get_json(silent=True) or {}
    text, metadata = _extract_text_callback_payload(data)
    if not text:
        return jsonify({
            "ok": False,
            "error": "Missing text-like field. Accepted: text, query, utterance, message, payload.text, payload.query, intent.query, request.text, request.query",
        }), 400

    try:
        result = speak(
            text=text,
            config=APP_CONFIG,
            config_path=APP_CONFIG_PATH,
            audio_base_url_override=_resolve_audio_base_url(),
        )
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc), "callback": metadata}), 500

    return jsonify({
        "ok": True,
        "accepted": True,
        "mode": "text_callback",
        "callback": metadata,
        "recognized_text": text,
        "speak_result": result,
        "reply_text": text,
    })


@app.get("/audio/<path:filename>")
def audio_file(filename: str) -> Any:
    if not APP_CONFIG_PATH:
        return jsonify({"ok": False, "error": "Server config is not loaded"}), 500

    tts = APP_CONFIG.get("tts") or {}
    output_dir = Path(tts.get("output_dir", "./tmp_audio"))
    if not output_dir.is_absolute():
        output_dir = (APP_CONFIG_PATH.parent / output_dir).resolve()

    return send_from_directory(output_dir, filename)


def main() -> None:
    global APP_CONFIG, APP_CONFIG_PATH

    parser = argparse.ArgumentParser(description="Run local HTTP bridge for tmall-genie-voice-bridge.")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).resolve().parents[1] / "config.json"),
        help="Path to config JSON file",
    )
    args = parser.parse_args()

    APP_CONFIG_PATH = Path(args.config).resolve()
    APP_CONFIG = load_config(APP_CONFIG_PATH)

    host = APP_CONFIG.get("host", "127.0.0.1")
    port = int(APP_CONFIG.get("port", 57881))
    app.run(host=host, port=port)


if __name__ == "__main__":
    main()
