from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import urlsplit, urlunsplit

from flask import Flask, jsonify, request, send_from_directory

CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from speak import load_config, speak


app = Flask(__name__)
APP_CONFIG: Dict[str, Any] = {}
APP_CONFIG_PATH: Path | None = None


def _request_external_base_url() -> str:
    proto = str(request.headers.get("X-Forwarded-Proto") or request.scheme).split(",")[0].strip()
    host = str(request.headers.get("X-Forwarded-Host") or request.host).split(",")[0].strip()
    prefix = str(request.headers.get("X-Forwarded-Prefix") or "").split(",")[0].strip().strip("/")

    base = f"{proto}://{host}"
    if prefix:
        base = f"{base}/{prefix}"
    return base.rstrip("/")


def _join_base_url(base_url: str, suffix_path: str) -> str:
    parsed = urlsplit(base_url.rstrip("/"))
    joined_path = parsed.path.rstrip("/") + "/" + suffix_path.lstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, joined_path, parsed.query, parsed.fragment))


def _resolve_audio_base_url() -> str | None:
    http_player = APP_CONFIG.get("http_player") or {}
    configured = str(http_player.get("audio_base_url") or "").strip()
    public_base_url = str(http_player.get("public_base_url") or "").strip()

    if public_base_url:
        return _join_base_url(public_base_url, "audio")

    if not configured:
        return None

    lowered = configured.lower()
    if lowered == "auto":
        return _join_base_url(_request_external_base_url(), "audio")

    return configured


def _expand_dotted_keys(data: Dict[str, Any]) -> Dict[str, Any]:
    expanded: Dict[str, Any] = {}
    for key, value in data.items():
        if "." not in key:
            expanded[key] = value
            continue

        node = expanded
        parts = key.split(".")
        for part in parts[:-1]:
            existing = node.get(part)
            if not isinstance(existing, dict):
                existing = {}
                node[part] = existing
            node = existing
        node[parts[-1]] = value
    return expanded


def _coerce_request_payload() -> Dict[str, Any]:
    payload: Dict[str, Any] = {}

    json_payload = request.get_json(silent=True)
    if isinstance(json_payload, dict):
        payload.update(json_payload)
    elif isinstance(json_payload, str) and json_payload.strip():
        payload["text"] = json_payload.strip()

    form_payload = request.form.to_dict(flat=True)
    if form_payload:
        payload.update(_expand_dotted_keys(form_payload))

    query_payload = request.args.to_dict(flat=True)
    if query_payload:
        payload.update(_expand_dotted_keys(query_payload))

    raw_text = request.get_data(as_text=True).strip()
    if raw_text:
        parsed_from_raw: Dict[str, Any] | None = None
        if not payload:
            try:
                raw_json = json.loads(raw_text)
            except json.JSONDecodeError:
                raw_json = None

            if isinstance(raw_json, dict):
                parsed_from_raw = raw_json
                payload.update(raw_json)
            elif isinstance(raw_json, str) and raw_json.strip():
                payload["text"] = raw_json.strip()

        if "text" not in payload and parsed_from_raw is None:
            payload["text"] = raw_text

    return payload


def _extract_text_value(data: Dict[str, Any]) -> str:
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
    return text


def _extract_text_callback_payload(data: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    text = _extract_text_value(data)
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
    data = _coerce_request_payload()
    text = _extract_text_value(data)
    if not text:
        return jsonify({"ok": False, "error": "Missing required field: text"}), 400

    try:
        result = speak(
            text=text,
            config=APP_CONFIG,
            config_path=APP_CONFIG_PATH,
            audio_base_url_override=_resolve_audio_base_url(),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500
    return jsonify(result)


@app.post("/callback/text")
@app.post("/webhook/text")
def text_callback_route() -> Any:
    data = _coerce_request_payload()
    text, metadata = _extract_text_callback_payload(data)
    if not text:
        return jsonify({
            "ok": False,
            "error": (
                "Missing text-like field. Accepted: text, query, utterance, message, "
                "payload.text, payload.query, intent.query, request.text, request.query."
            ),
        }), 400

    try:
        result = speak(
            text=text,
            config=APP_CONFIG,
            config_path=APP_CONFIG_PATH,
            audio_base_url_override=_resolve_audio_base_url(),
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc), "callback": metadata}), 400
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
