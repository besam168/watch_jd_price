from __future__ import annotations

import asyncio
from pathlib import Path


async def synthesize_to_file(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    try:
        import edge_tts  # type: ignore
    except ImportError as exc:
        raise RuntimeError("未安装 edge-tts。先执行: pip install edge-tts") from exc

    output_path.parent.mkdir(parents=True, exist_ok=True)
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicator.save(str(output_path))
    return output_path


def synthesize_sync(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    return asyncio.run(synthesize_to_file(text=text, output_path=output_path, voice=voice, rate=rate))
