from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import PlaybackBackend


class LocalWindowsSpeakerBackend(PlaybackBackend):
    def play(self, *, text: str, audio_path: Path, audio_url: str | None = None) -> Dict[str, Any]:
        script_path = self._resolve_script_path()
        timeout_seconds = int(self.options.get("timeout_seconds", 20))

        command = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-AudioPath",
            str(audio_path),
            "-TimeoutSeconds",
            str(timeout_seconds),
        ]

        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            stderr = result.stderr.strip() or "No stderr output"
            stdout = result.stdout.strip() or "No stdout output"
            raise RuntimeError(
                "local_windows_speaker failed "
                f"(exit_code={result.returncode}). stderr: {stderr}; stdout: {stdout}"
            )

        return {
            "ok": True,
            "backend": "local_windows_speaker",
            "audio_path": str(audio_path),
            "audio_url": audio_url,
            "stdout": (result.stdout or "").strip(),
        }

    def _resolve_script_path(self) -> Path:
        configured = self.options.get("player_script", "./scripts/play-local-audio.ps1")
        script_path = Path(configured)

        if script_path.is_absolute():
            resolved = script_path
        else:
            base_dirs = []
            config_dir = self.options.get("config_dir")
            if config_dir:
                base_dirs.append(Path(str(config_dir)))

            skill_dir = self.options.get("skill_dir")
            if skill_dir:
                base_dirs.append(Path(str(skill_dir)))

            resolved = None
            for base_dir in base_dirs:
                candidate = (base_dir / script_path).resolve()
                if candidate.exists():
                    resolved = candidate
                    break

            if resolved is None:
                resolved = (Path(".") / script_path).resolve()

        if not resolved.exists():
            raise FileNotFoundError(f"local_windows_speaker script not found: {resolved}")

        return resolved

