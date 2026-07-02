"""Chunk-Overlap-Arithmetik: Token-Zählung stimmt exakt (ADR-004).

Aufbau: Sätze mit exakt bekannter Tokenzahl → Chunk-Größen und Overlap
sind vollständig vorhersagbar und werden hier nachgerechnet.
"""

from app.domain import PageText
from app.ingest.chunker import Chunker, count_tokens


def _sentence(i: int, tokens: int) -> str:
    """Satz mit exakt `tokens` Whitespace-Tokens, eindeutig markiert."""
    assert tokens >= 1
    return " ".join([f"s{i}w{j}" for j in range(tokens - 1)] + [f"s{i}end."])


def _chunks(sentence_tokens: list[int], chunk_size: int, overlap: int):
    text = " ".join(_sentence(i, t) for i, t in enumerate(sentence_tokens))
    return Chunker(chunk_size=chunk_size, overlap=overlap).chunk(
        [PageText(page=1, text=text)], document_id="d", document_name="t.txt"
    )


def test_exact_packing_without_overlap():
    # 6 Sätze à 5 Tokens, chunk_size=10, overlap=0 → exakt 3 Chunks à 10 Tokens.
    chunks = _chunks([5] * 6, chunk_size=10, overlap=0)
    assert len(chunks) == 3
    assert [count_tokens(c.text) for c in chunks] == [10, 10, 10]


def test_overlap_token_count_is_exact():
    # 4 Sätze à 5 Tokens, chunk_size=10, overlap=5:
    # Chunk 0 = s0+s1 (10 Tokens). Overlap trägt genau s1 (5 Tokens) weiter.
    # Chunk 1 = s1+s2, Chunk 2 = s2+s3.
    chunks = _chunks([5] * 4, chunk_size=10, overlap=5)
    assert len(chunks) == 3
    assert [count_tokens(c.text) for c in chunks] == [10, 10, 10]

    for previous, current in zip(chunks, chunks[1:], strict=False):
        prev_tokens = previous.text.split()
        cur_tokens = current.text.split()
        shared = [t for t in cur_tokens if t in prev_tokens]
        assert len(shared) == 5  # exakt ein 5-Token-Satz Overlap


def test_overlap_never_exceeds_configured_budget():
    # Sätze à 4 Tokens, overlap=6 → es passen maximal s (4 Tokens) ins Budget,
    # nie zwei Sätze (8 > 6). Overlap ist damit exakt 4 Tokens.
    chunks = _chunks([4] * 6, chunk_size=8, overlap=6)
    for previous, current in zip(chunks, chunks[1:], strict=False):
        prev_set = set(previous.text.split())
        shared = [t for t in current.text.split() if t in prev_set]
        assert len(shared) == 4


def test_step_arithmetic_chunk_count():
    # 20 Sätze à 5 = 100 Tokens. chunk_size=15 (3 Sätze), overlap=5 (1 Satz)
    # → Schrittweite 2 Sätze pro Chunk: Starts bei s0,s2,...,s18, letzter voll = s16?
    # Nachgerechnet: Chunks = ceil((20 - 3) / 2) + 1 = 10 (Restsätze bilden Endchunk).
    chunks = _chunks([5] * 20, chunk_size=15, overlap=5)
    assert len(chunks) == 10
    # Jeder volle Chunk: 3 Sätze à 5 Tokens = 15.
    assert all(count_tokens(c.text) == 15 for c in chunks[:-1])
    # Erster Satz jedes Chunks rückt um genau 2 Sätze vor.
    first_words = [c.text.split()[0] for c in chunks]
    assert first_words == [f"s{2 * i}w0" for i in range(10)]
