from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit

import requests


def load_config(config_path: Path) -> Dict[str, Any]:
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8-sig"))


def _string(value: Any) -> str:
    return "" if value is None else str(value)


def _looks_local_or_placeholder(value: str, placeholders: List[str]) -> bool:
    normalized = _string(value).strip()
    if not normalized:
        return False
    lowered = normalized.lower()
    if "127.0.0.1" in lowered or "localhost" in lowered:
        return True
    return any(token.lower() in lowered for token in placeholders)


def evaluate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    warnings: List[str] = []

    backend_type = _string((config.get("backend") or {}).get("type"))
    player_url = _string((config.get("http_player") or {}).get("player_url")).strip()
    audio_base_url = _string((config.get("http_player") or {}).get("audio_base_url")).strip()
    public_base_url = _string((config.get("http_player") or {}).get("public_base_url")).strip()
    entity_id = _string((((config.get("http_player") or {}).get("body_template") or {}).get("entity_id"))).strip()
    auth_header = _string((((config.get("http_player") or {}).get("headers") or {}).get("Authorization"))).strip()
    host = _string(config.get("host")).strip()
    port = config.get("port")
    tts_provider = _string((config.get("tts") or {}).get("provider")).strip()

    checks: Dict[str, Any] = {
        "host": host or None,
        "port": port,
        "backend": backend_type or None,
        "player_url": player_url or None,
        "audio_base_url": audio_base_url or None,
        "public_base_url": public_base_url or None,
        "entity_id": entity_id or None,
        "tts_provider": tts_provider or None,
    }

    if backend_type != "local_http_player":
        issues.append("backend.type must be 'local_http_player' for real HTTP playback")

    if not player_url:
        issues.append("http_player.player_url is required")
    elif _looks_local_or_placeholder(player_url, ["HOME_ASSISTANT_HOST", "YOUR_PLAYER_HOST"]):
        warnings.append("http_player.player_url still looks local or placeholder; verify the playback controller can actually be reached")

    if not auth_header:
        warnings.append("http_player.headers.Authorization is empty")
    elif "REPLACE" in auth_header.upper():
        issues.append("http_player.headers.Authorization still contains placeholder text")

    if not entity_id:
        issues.append("http_player.body_template.entity_id is required")
    elif entity_id == "media_player.tmall_genie" or "REPLACE_ME" in entity_id:
        warnings.append("entity_id is still the example/default value; verify it matches the real target entity")

    if not public_base_url and not audio_base_url:
        issues.append("set http_player.public_base_url or audio_base_url so the playback target can fetch /audio/...")

    if public_base_url and _looks_local_or_placeholder(public_base_url, ["BRIDGE_HOST", "YOUR_BRIDGE_PUBLIC_HOST"]):
        warnings.append("http_player.public_base_url still looks placeholder/local; remote players usually cannot fetch audio from it")

    if audio_base_url.lower() == "auto" and host.lower() in {"127.0.0.1", "localhost"}:
        warnings.append("audio_base_url='auto' depends on the incoming host; if the bridge is only bound locally, remote playback will fail")

    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "checks": checks,
    }


def probe_runtime(config: Dict[str, Any], *, timeout: int = 3) -> Dict[str, Any]:
    runtime: Dict[str, Any] = {
        "bridge_health": None,
        "player_probe": None,
    }

    warnings: List[str] = []
    host = _string(config.get("host")).strip()
    port = config.get("port")
    if host and port:
        health_url = f"http://{host}:{port}/health"
        try:
            response = requests.get(health_url, timeout=timeout)
            runtime["bridge_health"] = {
                "ok": True,
                "status_code": response.status_code,
                "url": health_url,
            }
        except Exception as exc:
            runtime["bridge_health"] = {
                "ok": False,
                "error": str(exc),
            }
            warnings.append("bridge health endpoint not reachable right now; start the bridge before real testing")

    player_url = _string((config.get("http_player") or {}).get("player_url")).strip()
    if player_url and not _looks_local_or_placeholder(player_url, ["HOME_ASSISTANT_HOST", "YOUR_PLAYER_HOST"]):
        try:
            parsed = urlsplit(player_url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            response = requests.get(base_url, timeout=timeout)
            runtime["player_probe"] = {
                "ok": True,
                "status_code": response.status_code,
                "base": base_url,
            }
        except Exception as exc:
            runtime["player_probe"] = {
                "ok": False,
                "base": f"{parsed.scheme}://{parsed.netloc}" if 'parsed' in locals() else None,
                "error": str(exc),
            }
            warnings.append("playback target base URL did not answer a quick probe; confirm host, port, firewall, and reverse proxy")

    return {
        "runtime": runtime,
        "warnings": warnings,
    }


def run_preflight(config_path: Path, *, probe: bool = True, timeout: int = 3) -> Dict[str, Any]:
    config = load_config(config_path)
    result = evaluate_config(config)
    result["checks"]["config"] = str(config_path)
    if probe:
        probe_result = probe_runtime(config, timeout=timeout)
        result["checks"].update(probe_result["runtime"])
        result["warnings"].extend(probe_result["warnings"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Preflight checker for real HTTP playback targets.")
    parser.add_argument("--config", required=True, help="Path to config JSON file")
    parser.add_argument("--no-probe", action="store_true", help="Skip runtime HTTP probes")
    parser.add_argument("--timeout", type=int, default=3, help="Probe timeout in seconds")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    result = run_preflight(config_path, probe=not args.no_probe, timeout=args.timeout)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
