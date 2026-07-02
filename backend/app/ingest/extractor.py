"""TextExtractor — Strategy je Dateityp (ADR-007).

PDF und Plaintext decken den MVP ab; Word wäre eine weitere Strategy-Klasse.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod

from app.domain import PageText
from app.errors import EmptyDocumentError


class TextExtractor(ABC):
    """Rohdaten → Seitentexte. Wirft EmptyDocumentError bei leerem Ergebnis."""

    @abstractmethod
    def extract(self, data: bytes) -> list[PageText]: ...


class PlainTextExtractor(TextExtractor):
    """UTF-8 mit Latin-1-Fallback; Plaintext ist immer 'Seite 1'."""

    def extract(self, data: bytes) -> list[PageText]:
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        text = text.strip()
        if not text:
            raise EmptyDocumentError("Dokument enthält keinen Text.")
        return [PageText(page=1, text=text)]


class PdfExtractor(TextExtractor):
    """pypdf-basierte Extraktion, Seitennummern bleiben erhalten (Zitat-Metadatum)."""

    def extract(self, data: bytes) -> list[PageText]:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(data))
        pages = [
            PageText(page=i + 1, text=text)
            for i, raw in enumerate(reader.pages)
            if (text := (raw.extract_text() or "").strip())
        ]
        if not pages:
            raise EmptyDocumentError(
                "PDF enthält keinen extrahierbaren Text (evtl. reiner Scan)."
            )
        return pages
