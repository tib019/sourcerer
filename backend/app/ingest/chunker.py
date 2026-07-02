"""Chunker — Token-basiertes Sliding-Window mit Satzgrenzen-Präferenz (ADR-004).

Token = Whitespace-Token (deterministisch, exakt testbar — kein Tokenizer-Zoo).
Strategie:
  1. Text in Sätze splitten (Satzende: . ! ? gefolgt von Whitespace).
  2. Sätze greedy in Chunks packen, bis chunk_size Tokens erreicht wären.
  3. Overlap: der nächste Chunk beginnt mit den letzten Sätzen des vorherigen,
     deren Tokensumme <= overlap ist.
  4. Ein Einzelsatz > chunk_size wird hart in chunk_size-Stücke geschnitten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.domain import Chunk, PageText, new_id
from app.errors import EmptyDocumentError

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def count_tokens(text: str) -> int:
    """Whitespace-Token-Zählung — die eine Definition, die überall gilt."""
    return len(text.split())


@dataclass(frozen=True)
class _Sentence:
    text: str
    page: int
    tokens: int


class Chunker:
    def __init__(self, chunk_size: int = 800, overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size muss > 0 sein")
        if not 0 <= overlap < chunk_size:
            raise ValueError("overlap muss in [0, chunk_size) liegen")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(
        self, pages: list[PageText], *, document_id: str, document_name: str
    ) -> list[Chunk]:
        sentences = self._sentences(pages)
        if not sentences:
            raise EmptyDocumentError("Dokument enthält keinen Text.")

        groups: list[list[_Sentence]] = []
        current: list[_Sentence] = []
        current_tokens = 0

        for sentence in sentences:
            if current and current_tokens + sentence.tokens > self.chunk_size:
                groups.append(current)
                current = self._carry_overlap(current)
                current_tokens = sum(s.tokens for s in current)
            current.append(sentence)
            current_tokens += sentence.tokens
        if current:
            groups.append(current)

        return [
            Chunk(
                id=new_id(),
                document_id=document_id,
                document_name=document_name,
                chunk_index=i,
                page=group[0].page,
                text=" ".join(s.text for s in group),
            )
            for i, group in enumerate(groups)
        ]

    def _carry_overlap(self, group: list[_Sentence]) -> list[_Sentence]:
        """Letzte Sätze mit Tokensumme <= overlap — Kontext über die Grenze hinweg."""
        carried: list[_Sentence] = []
        total = 0
        for sentence in reversed(group):
            if total + sentence.tokens > self.overlap:
                break
            carried.insert(0, sentence)
            total += sentence.tokens
        return carried

    def _sentences(self, pages: list[PageText]) -> list[_Sentence]:
        sentences: list[_Sentence] = []
        for page in pages:
            for raw in _SENTENCE_END.split(page.text):
                text = " ".join(raw.split())  # Whitespace normalisieren
                if not text:
                    continue
                tokens = count_tokens(text)
                if tokens > self.chunk_size:
                    sentences.extend(self._hard_split(text, page.page))
                else:
                    sentences.append(_Sentence(text=text, page=page.page, tokens=tokens))
        return sentences

    def _hard_split(self, text: str, page: int) -> list[_Sentence]:
        words = text.split()
        return [
            _Sentence(
                text=" ".join(words[i : i + self.chunk_size]),
                page=page,
                tokens=len(words[i : i + self.chunk_size]),
            )
            for i in range(0, len(words), self.chunk_size)
        ]
