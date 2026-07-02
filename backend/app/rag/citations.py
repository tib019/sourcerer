"""CitationMapper — [n]-Referenzen ↔ Chunk-Metadaten (ADR-005).

Verwirft Referenzen auf nicht existierende Quellen ([99]) — das ist ein
Halluzinations-Symptom und wird damit sichtbar statt stumm durchgereicht.
"""

from __future__ import annotations

import re

from app.domain import ChatAnswer, Citation, ScoredChunk
from app.providers.llm import NO_ANSWER

_MARKER = re.compile(r"\[(\d+)\]")


class CitationMapper:
    def map(self, answer_text: str, chunks: list[ScoredChunk]) -> ChatAnswer:
        if NO_ANSWER in answer_text:
            return ChatAnswer(text=NO_ANSWER, citations=[])

        valid = range(1, len(chunks) + 1)
        seen: list[int] = []
        for match in _MARKER.finditer(answer_text):
            n = int(match.group(1))
            if n in valid and n not in seen:
                seen.append(n)

        # Ungültige Marker aus dem Text entfernen, gültige stehen lassen.
        cleaned = _MARKER.sub(
            lambda m: m.group(0) if int(m.group(1)) in valid else "", answer_text
        ).strip()

        citations = [
            Citation(
                n=n,
                document_id=chunks[n - 1].chunk.document_id,
                document_name=chunks[n - 1].chunk.document_name,
                chunk_index=chunks[n - 1].chunk.chunk_index,
                page=chunks[n - 1].chunk.page,
                text=chunks[n - 1].chunk.text,
            )
            for n in seen
        ]
        return ChatAnswer(text=cleaned, citations=citations)
