"""TTSProvider — ABC + OpenAI-TTS und deterministischer Fake (ADR-008).

Der Fake erzeugt ein echtes, abspielbares WAV (Sinuston) — damit funktionieren
Player, API-Tests und E2E komplett offline, ohne Audio-Fixture im Repo.
"""

from __future__ import annotations

import io
import logging
import math
import struct
import wave
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger("sourcerer.providers")


@dataclass(frozen=True)
class Speech:
    audio: bytes
    media_type: str


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> Speech: ...


class OpenAITTS(TTSProvider):
    """OpenAI TTS (tts-1) — ein API-Call, MP3 zurück (CONTEXT §3)."""

    MODEL = "tts-1"
    VOICE = "alloy"
    _USD_PER_1M_CHARS = 15.0

    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    def synthesize(self, text: str) -> Speech:
        response = self._client.audio.speech.create(
            model=self.MODEL, voice=self.VOICE, input=text
        )
        logger.info(
            "tts: %d Zeichen (~$%.6f)", len(text), len(text) / 1_000_000 * self._USD_PER_1M_CHARS
        )
        return Speech(audio=response.content, media_type="audio/mpeg")


class FakeTTS(TTSProvider):
    """Deterministischer Stub: 0,8 s Sinuston als valides WAV, Länge ∝ Textlänge."""

    _SAMPLE_RATE = 16_000

    def synthesize(self, text: str) -> Speech:
        seconds = min(0.4 + len(text) / 2000, 2.0)
        n_samples = int(self._SAMPLE_RATE * seconds)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self._SAMPLE_RATE)
            wav.writeframes(
                b"".join(
                    struct.pack(
                        "<h",
                        int(12_000 * math.sin(2 * math.pi * 440 * i / self._SAMPLE_RATE)),
                    )
                    for i in range(n_samples)
                )
            )
        return Speech(audio=buffer.getvalue(), media_type="audio/wav")
