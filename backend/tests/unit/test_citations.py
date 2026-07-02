"""CitationMapper-Tests: [n]-Referenz → korrekter Chunk, Halluzinations-Marker, No-Answer."""

from app.domain import Chunk, ScoredChunk
from app.providers.llm import NO_ANSWER
from app.rag.citations import CitationMapper


def _chunks(n: int) -> list[ScoredChunk]:
    return [
        ScoredChunk(
            chunk=Chunk(
                id=f"c{i}",
                document_id=f"doc{i}",
                document_name=f"datei{i}.txt",
                chunk_index=i,
                page=i + 1,
                text=f"Inhalt von Chunk {i}.",
            ),
            score=1.0 - i * 0.1,
        )
        for i in range(n)
    ]


def test_maps_reference_to_correct_chunk():
    answer = CitationMapper().map("Die Antwort steht hier [2].", _chunks(3))
    assert len(answer.citations) == 1
    citation = answer.citations[0]
    assert citation.n == 2
    assert citation.document_id == "doc1"  # [2] = zweiter Chunk = Index 1
    assert citation.page == 2
    assert citation.text == "Inhalt von Chunk 1."


def test_multiple_references_deduplicated_in_order():
    answer = CitationMapper().map("A [3], B [1], nochmal [3].", _chunks(3))
    assert [c.n for c in answer.citations] == [3, 1]


def test_invalid_reference_is_dropped_and_stripped():
    answer = CitationMapper().map("Erfunden [99], echt [1].", _chunks(2))
    assert [c.n for c in answer.citations] == [1]
    assert "[99]" not in answer.text
    assert "[1]" in answer.text


def test_no_answer_yields_no_citations():
    answer = CitationMapper().map(f"{NO_ANSWER} [1]", _chunks(2))
    assert answer.text == NO_ANSWER
    assert answer.citations == []


def test_answer_without_references():
    answer = CitationMapper().map("Text ohne Marker.", _chunks(2))
    assert answer.citations == []
    assert answer.text == "Text ohne Marker."
