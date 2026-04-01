from __future__ import annotations

import math
import struct
import wave
from pathlib import Path


def synthesize_sync(*, text: str, output_path: Path, voice: str, rate: str = "+0%") -> Path:
    del text, voice, rate

    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_rate = 24000
    duration_seconds = 0.35
    frequency = 880.0
    amplitude = 0.3

    frame_count = int(sample_rate * duration_seconds)
    pcm = bytearray()
    for i in range(frame_count):
        t = i / sample_rate
        sample = amplitude * math.sin(2 * math.pi * frequency * t)
        pcm.extend(struct.pack("<h", int(sample * 32767)))

    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(pcm))

    return output_path
