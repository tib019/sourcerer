"""Chunking-Unit-Tests: Größen, Overlap, Grenzen (leer, 1 Satz, Riesen-Doc)."""

import pytest

from app.domain import PageText
from app.errors import EmptyDocumentError
from app.ingest.chunker import Chunker, count_tokens


def _sentences(n: int, words_per_sentence: int = 5) -> str:
    """n Sätze mit exakt words_per_sentence Tokens: 'w1 w2 w3 w4 s0.' usw."""
    return " ".join(
        " ".join(f"w{j}" for j in range(words_per_sentence - 1)) + f" s{i}."
        for i in range(n)
    )


def _chunk(text: str, chunk_size: int, overlap: int):
    chunker = Chunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk(
        [PageText(page=1, text=text)], document_id="d1", document_name="test.txt"
    )


def test_empty_document_raises():
    with pytest.raises(EmptyDocumentError):
        _chunk("   \n\t  ", chunk_size=10, overlap=2)


def test_single_sentence_yields_single_chunk():
    chunks = _chunk("Ein einzelner kurzer Satz.", chunk_size=100, overlap=10)
    assert len(chunks) == 1
    assert chunks[0].text == "Ein einzelner kurzer Satz."
    assert chunks[0].chunk_index == 0


def test_no_chunk_exceeds_chunk_size():
    chunks = _chunk(_sentences(200), chunk_size=50, overlap=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert count_tokens(chunk.text) <= 50


def test_chunk_indices_are_sequential():
    chunks = _chunk(_sentences(100), chunk_size=30, overlap=5)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_full_text_is_covered():
    """Jeder Satz muss in mindestens einem Chunk auftauchen."""
    n = 50
    chunks = _chunk(_sentences(n), chunk_size=30, overlap=5)
    combined = " ".join(c.text for c in chunks)
    for i in range(n):
        assert f"s{i}." in combined


def test_oversized_sentence_is_hard_split():
    giant = " ".join(f"w{i}" for i in range(120)) + "."
    chunks = _chunk(giant, chunk_size=50, overlap=10)
    assert all(count_tokens(c.text) <= 50 for c in chunks)
    combined = " ".join(c.text for c in chunks)
    assert "w0" in combined and "w119" in combined


def test_page_metadata_tracks_first_sentence():
    pages = [
        PageText(page=1, text=_sentences(4)),
        PageText(page=2, text=_sentences(4).replace("s", "p")),
    ]
    chunker = Chunker(chunk_size=1000, overlap=0)
    chunks = chunker.chunk(pages, document_id="d1", document_name="test.pdf")
    assert chunks[0].page == 1

    small = Chunker(chunk_size=20, overlap=0).chunk(
        pages, document_id="d1", document_name="test.pdf"
    )
    assert small[0].page == 1
    assert small[-1].page == 2


def test_invalid_parameters_rejected():
    with pytest.raises(ValueError):
        Chunker(chunk_size=0, overlap=0)
    with pytest.raises(ValueError):
        Chunker(chunk_size=10, overlap=10)
    with pytest.raises(ValueError):
        Chunker(chunk_size=10, overlap=-1)
