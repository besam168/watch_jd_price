from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict


class PlaybackBackend(ABC):
    def __init__(self, options: Dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def play(self, *, text: str, audio_path: Path, audio_url: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError
