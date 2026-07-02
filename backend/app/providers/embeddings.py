"""EmbeddingProvider — ABC + OpenAI- und deterministische Fake-Implementierung (ADR-006)."""

from __future__ import annotations

import hashlib
import logging
import math
from abc import ABC, abstractmethod

logger = logging.getLogger("sourcerer.providers")


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int: ...

    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]: ...


class OpenAIEmbeddings(EmbeddingProvider):
    """text-embedding-3-small (1536 Dim.), mit Token-Logging pro Call (NOTES §6)."""

    MODEL = "text-embedding-3-small"
    _DIMENSION = 1536
    _USD_PER_1M_TOKENS = 0.02

    def __init__(self, api_key: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)

    @property
    def dimension(self) -> int:
        return self._DIMENSION

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.MODEL, input=texts)
        tokens = response.usage.total_tokens
        logger.info(
            "embeddings: %d Texte, %d Tokens (~$%.6f)",
            len(texts), tokens, tokens / 1_000_000 * self._USD_PER_1M_TOKENS,
        )
        return [item.embedding for item in response.data]


class FakeEmbeddings(EmbeddingProvider):
    """Deterministisches Hashed-Bag-of-Words-Embedding.

    Jedes Wort wird stabil (md5) auf eine Dimension gehasht, gezählt, L2-normalisiert.
    Texte mit gemeinsamen Wörtern bekommen hohe Cosine-Similarity — Retrieval
    funktioniert damit offline, reproduzierbar und kostenfrei (Tests, CI, Demo).
    """

    def __init__(self, dimension: int = 64) -> None:
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self._dimension
        for word in text.lower().split():
            word = word.strip(".,;:!?()[]{}\"'«»„“”")
            if not word:
                continue
            digest = hashlib.md5(word.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self._dimension
            vector[index] += 1.0
        norm = math.sqrt(sum(v * v for v in vector))
        return [v / norm for v in vector] if norm else vector
