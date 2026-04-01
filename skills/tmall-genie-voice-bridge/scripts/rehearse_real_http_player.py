from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

import requests

from preflight_real_http_player import run_preflight


DEFAULT_TEXT = "真实 HTTP 播放联调演练"


def _safe_json_response(response: requests.Response) -> Any:
    try:
        return response.json()
    except ValueError:
        return response.text


def summarize_bridge_call(*, response: requests.Response | None = None, error: Exception | None = None) -> Dict[str, Any]:
    if error is not None:
        return {
            "ok": False,
            "transport_error": str(error),
            "http_status": None,
            "bridge_ok": None,
            "backend": None,
            "audio_url": None,
            "target_status": None,
            "player_url": None,
            "response": None,
        }

    assert response is not None
    payload = _safe_json_response(response)
    if not isinstance(payload, dict):
        payload = {"raw": payload}

    return {
        "ok": response.ok,
        "transport_error": None,
        "http_status": response.status_code,
        "bridge_ok": payload.get("ok") if isinstance(payload, dict) else None,
        "backend": payload.get("backend") or ((payload.get("speak_result") or {}).get("backend") if isinstance(payload.get("speak_result"), dict) else None),
        "audio_url": payload.get("audio_url") or ((payload.get("speak_result") or {}).get("audio_url") if isinstance(payload.get("speak_result"), dict) else None),
        "target_status": payload.get("target_status"),
        "player_url": payload.get("player_url"),
        "response": payload,
    }


def run_rehearsal(
    *,
    config_path: Path,
    bridge_url: str,
    text: str,
    timeout: int = 20,
    skip_probe: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    preflight = run_preflight(config_path, probe=not skip_probe)

    result: Dict[str, Any] = {
        "ok": False,
        "mode": "real_http_player_rehearsal",
        "config": str(config_path),
        "bridge_url": bridge_url,
        "text": text,
        "preflight": preflight,
        "request": None,
        "notes": [
            "This rehearsal only verifies config and HTTP handoff behavior.",
            "It does not prove that a real speaker or Tmall Genie hardware actually played audio.",
        ],
    }

    if not preflight.get("ok") and not force:
        result["request"] = {
            "ok": False,
            "skipped": True,
            "reason": "Preflight failed; rerun with --force to continue anyway.",
        }
        return result

    request_body = {"text": text}
    result["request_body"] = request_body

    try:
        response = requests.post(bridge_url, json=request_body, timeout=timeout)
        request_summary = summarize_bridge_call(response=response)
    except Exception as exc:
        request_summary = summarize_bridge_call(error=exc)

    result["request"] = request_summary
    result["ok"] = bool(preflight.get("ok")) and bool(request_summary.get("ok"))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run preflight plus one real /speak rehearsal against the configured HTTP player.")
    parser.add_argument("--config", required=True, help="Path to config JSON file")
    parser.add_argument("--bridge-url", default="http://127.0.0.1:57881/speak", help="Bridge /speak URL")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="Text to send to /speak")
    parser.add_argument("--timeout", type=int, default=20, help="POST timeout in seconds")
    parser.add_argument("--skip-probe", action="store_true", help="Skip runtime HTTP probes during preflight")
    parser.add_argument("--force", action="store_true", help="Continue to /speak even if preflight finds blocking issues")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    result = run_rehearsal(
        config_path=config_path,
        bridge_url=args.bridge_url,
        text=args.text,
        timeout=args.timeout,
        skip_probe=args.skip_probe,
        force=args.force,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
