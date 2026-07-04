"""Gemeinsame Text-Normalisierung für die Fake-Provider (Embeddings + LLM).

Stopwörter tragen keine Bedeutung — sie erzeugen im Bag-of-Words nur
Kollisions-Ähnlichkeit zwischen völlig fremden Texten (empirisch gemessen:
scripts/calibrate_min_score.py, siehe NOTES §2).
"""

from __future__ import annotations

import re

STOPWORDS = frozenset(
    """der die das den dem des ein eine einer eines und oder ist sind war waren wird werden
    kann können hat haben in im an am auf aus bei mit von für zu zur zum nach über unter
    wie was wer wen wem wo wann warum welche welcher welches es er sie man nicht auch nur
    the a an of is are what who how where when why in on for with and or to
    heißt heisst gibt steht sagt macht viele mehr sehr dass wenn als
    """.split()
)

_WORD = re.compile(r"[\wäöüÄÖÜß-]+")


def content_words(text: str) -> set[str]:
    """Bedeutungstragende Wörter: lowercase, ohne Stopwörter, länger als 2 Zeichen."""
    return {
        w for w in (m.group(0).lower() for m in _WORD.finditer(text))
        if len(w) > 2 and w not in STOPWORDS
    }
