"""Konfiguration aus Env-Variablen — Keys ausschließlich server-seitig (NOTES §5)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


@dataclass(frozen=True)
class Settings:
    providers: str = field(
        default_factory=lambda: os.environ.get("SOURCERER_PROVIDERS", "fake")
    )
    openai_api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))
    pinecone_api_key: str = field(
        default_factory=lambda: os.environ.get("PINECONE_API_KEY", "")
    )
    pinecone_index: str = field(
        default_factory=lambda: os.environ.get("PINECONE_INDEX", "sourcerer")
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.environ.get("SOURCERER_CHUNK_SIZE", "800"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.environ.get("SOURCERER_CHUNK_OVERLAP", "120"))
    )
    top_k: int = field(default_factory=lambda: int(os.environ.get("SOURCERER_TOP_K", "6")))
    max_upload_bytes: int = field(
        default_factory=lambda: int(
            os.environ.get("SOURCERER_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))
        )
    )
    cors_origins: list[str] = field(
        default_factory=lambda: _split_origins(
            os.environ.get("SOURCERER_CORS_ORIGINS", "http://localhost:3000")
        )
    )

    def validate(self) -> None:
        if self.providers not in ("fake", "openai"):
            raise ValueError("SOURCERER_PROVIDERS muss 'fake' oder 'openai' sein")
        if self.providers == "openai":
            missing = [
                name
                for name, value in (
                    ("OPENAI_API_KEY", self.openai_api_key),
                    ("PINECONE_API_KEY", self.pinecone_api_key),
                )
                if not value
            ]
            if missing:
                raise ValueError(f"Fehlende Env-Variablen: {', '.join(missing)}")
