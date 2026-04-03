from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path


async def synthesize_to_file(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    try:
        import edge_tts  # type: ignore
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed. Run: pip install edge-tts") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)

    target_ext = output_path.suffix.lower()
    edge_output_path = output_path
    temp_mp3_path: Path | None = None

    if target_ext == ".wav":
        temp_mp3_path = output_path.with_suffix(".edge-temp.mp3")
        edge_output_path = temp_mp3_path

    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicator.save(str(edge_output_path))

    if target_ext == ".wav":
        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            raise RuntimeError("ffmpeg is required to convert edge-tts output to wav, but it was not found in PATH")

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(temp_mp3_path),
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            "16000",
            str(output_path),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            raise RuntimeError(
                "ffmpeg failed to convert edge-tts mp3 to wav. "
                f"stderr: {stderr or 'No stderr output'}; stdout: {stdout or 'No stdout output'}"
            )

        try:
            temp_mp3_path.unlink(missing_ok=True)
        except Exception:
            pass

    return output_path


def synthesize_sync(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    return asyncio.run(synthesize_to_file(text=text, output_path=output_path, voice=voice, rate=rate))
