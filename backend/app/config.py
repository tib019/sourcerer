"""Konfiguration aus Env-Variablen — Keys ausschließlich server-seitig (NOTES §5)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _split_origins(raw: str) -> list[str]:
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


# Retrieval-Mindest-Score (Cosine) — NUR ein Rausch-Floor, kein Relevanz-Urteil.
# Empirie (scripts/calibrate_min_score.py + Produktions-Incident, ADR-004):
# Toy-Golden-Set trennte sauber (0.21 vs 0.39 -> 0.30), aber echte Kurz-Queries
# brachen das: in-source "Ideologie" top1=0.12, "Stufe 1" (cross-lingual)=0.21,
# waehrend out-of-source Fragen bis 0.21 scoren. KEIN Skalarwert trennt beides ->
# Threshold filtert nur noch Rauschen, Groundedness entscheidet der Prompt (LLM).
OPENAI_MIN_SCORE = 0.05
# Fake-Provider ist ein deterministischer Test-Stub mit eigener Score-Verteilung —
# bewusst NICHT kalibriert, nur ein Boden gegen Null-Treffer.
FAKE_MIN_SCORE = 0.05


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
    supabase_url: str = field(default_factory=lambda: os.environ.get("SUPABASE_URL", ""))
    supabase_key: str = field(default_factory=lambda: os.environ.get("SUPABASE_KEY", ""))
    chunk_size: int = field(
        default_factory=lambda: int(os.environ.get("SOURCERER_CHUNK_SIZE", "800"))
    )
    chunk_overlap: int = field(
        default_factory=lambda: int(os.environ.get("SOURCERER_CHUNK_OVERLAP", "120"))
    )
    top_k: int = field(default_factory=lambda: int(os.environ.get("SOURCERER_TOP_K", "6")))
    min_score_override: float | None = field(
        default_factory=lambda: (
            float(raw) if (raw := os.environ.get("SOURCERER_MIN_SCORE")) else None
        )
    )
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

    @property
    def min_score(self) -> float:
        if self.min_score_override is not None:
            return self.min_score_override
        return OPENAI_MIN_SCORE if self.providers == "openai" else FAKE_MIN_SCORE

    def validate(self) -> None:
        if self.providers not in ("fake", "openai"):
            raise ValueError("SOURCERER_PROVIDERS muss 'fake' oder 'openai' sein")
        if self.providers == "openai":
            missing = [
                name
                for name, value in (
                    ("OPENAI_API_KEY", self.openai_api_key),
                    ("PINECONE_API_KEY", self.pinecone_api_key),
                    ("SUPABASE_URL", self.supabase_url),
                    ("SUPABASE_KEY", self.supabase_key),
                )
                if not value
            ]
            if missing:
                raise ValueError(f"Fehlende Env-Variablen: {', '.join(missing)}")
