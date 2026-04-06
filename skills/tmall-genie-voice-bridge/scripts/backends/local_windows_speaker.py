from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

from .base import PlaybackBackend


class LocalWindowsSpeakerBackend(PlaybackBackend):
    def play(self, *, text: str, audio_path: Path, audio_url: str | None = None) -> Dict[str, Any]:
        del text

        timeout_seconds = int(self.options.get("timeout_seconds", 20))
        config_dir = Path(str(self.options.get("config_dir") or ".")).resolve()
        player_script = str(self.options.get("player_script") or "").strip()

        if player_script:
            script_path = Path(player_script)
            if not script_path.is_absolute():
                script_path = (config_dir / script_path).resolve()

            if not script_path.is_file():
                raise RuntimeError(f"Configured local_windows_speaker.player_script not found: {script_path}")

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
        else:
            extension = audio_path.suffix.lower()
            if extension == ".wav":
                command_text = f"""
$ErrorActionPreference = 'Stop'
$audioFile = {str(audio_path)!r}
$player = New-Object System.Media.SoundPlayer $audioFile
$player.Load()
$player.PlaySync()
Write-Output 'PLAYBACK_CONFIRMED=1'
Write-Output 'PLAYBACK_BACKEND=SoundPlayer'
Write-Output 'PLAYSTATE_FINAL=WAV_SYNC_OK'
"""
            else:
                command_text = f"""
$ErrorActionPreference = 'Stop'
$audioFile = {str(audio_path)!r}
$TimeoutSeconds = {timeout_seconds}
$wmp = New-Object -ComObject WMPlayer.OCX
$wmp.settings.autoStart = $false
$wmp.settings.volume = 100
$wmp.URL = $audioFile
$wmp.controls.play()
$stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$started = $false
while ($stopwatch.Elapsed.TotalSeconds -lt $TimeoutSeconds) {{
  $state = [int]$wmp.playState
  if ($state -eq 3) {{ $started = $true }}
  if ($started -and ($state -eq 1 -or $state -eq 8)) {{
    Write-Output 'PLAYBACK_CONFIRMED=1'
    Write-Output 'PLAYBACK_BACKEND=WMPlayerCOM'
    Write-Output 'PLAYSTATE_FINAL=OK'
    exit 0
  }}
  Start-Sleep -Milliseconds 150
}}
if ($started) {{
  Write-Output 'PLAYBACK_CONFIRMED=1'
  Write-Output 'PLAYBACK_BACKEND=WMPlayerCOM'
  Write-Output 'PLAYSTATE_FINAL=TIMEOUT_AFTER_START'
  exit 0
}}
throw 'WMPlayer COM did not enter playing state before timeout.'
"""

            command = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                command_text,
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
            "player_script_used": bool(player_script),
        }

