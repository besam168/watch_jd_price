from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .base import PlaybackBackend


class MockTmallGenieBackend(PlaybackBackend):
    def play(self, *, text: str, audio_path: Path, audio_url: str | None = None) -> Dict[str, Any]:
        return {
            "ok": True,
            "backend": "mock_tmall_genie",
            "device_name": self.options.get("device_name", "Tmall-Genie"),
            "device_ip": self.options.get("device_ip", "unknown"),
            "text": text,
            "audio_path": str(audio_path),
            "audio_url": audio_url,
            "played_at": datetime.now().isoformat(timespec="seconds"),
            "note": "这是模拟后端：链路已打通，但未真正下发到天猫精灵。"
        }
