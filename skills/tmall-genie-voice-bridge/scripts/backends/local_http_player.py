from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import requests

from .base import PlaybackBackend


class LocalHttpPlayerBackend(PlaybackBackend):
    def play(self, *, text: str, audio_path: Path, audio_url: str | None = None) -> Dict[str, Any]:
        if not audio_url:
            raise ValueError("local_http_player requires audio_url, but none was provided")

        player_url = self.options.get("player_url")
        if not player_url:
            raise ValueError("local_http_player requires http_player.player_url")

        headers = dict(self.options.get("headers") or {})
        method = str(self.options.get("method", "POST")).upper()
        timeout = int(self.options.get("timeout", 15))
        body_template = self.options.get("body_template") or {}
        payload = _replace_placeholders(body_template, text=text, audio_url=audio_url, audio_path=str(audio_path))

        response = requests.request(method=method, url=player_url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()

        return {
            "ok": True,
            "backend": "local_http_player",
            "player_url": player_url,
            "audio_url": audio_url,
            "status_code": response.status_code,
            "response_preview": response.text[:500],
        }


def _replace_placeholders(value: Any, **kwargs: str) -> Any:
    if isinstance(value, str):
        output = value
        for key, item in kwargs.items():
            output = output.replace("{{" + key + "}}", item)
        return output
    if isinstance(value, list):
        return [_replace_placeholders(v, **kwargs) for v in value]
    if isinstance(value, dict):
        return {k: _replace_placeholders(v, **kwargs) for k, v in value.items()}
    return value