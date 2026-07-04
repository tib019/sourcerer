"""Threshold-Pfad: NO_ANSWER muss aus dem Retrieval kommen, nicht nur aus dem Prompt.

Die Scores in diesen Tests sind die MESSWERTE der Kalibrierung gegen
text-embedding-3-small (scripts/calibrate_min_score.py, ADR-004):
  max(unbeantwortbar) = 0.2115   min(beantwortbar) = 0.3913   Threshold = 0.30
"""

from app.config import OPENAI_MIN_SCORE, Settings
from app.domain import Chunk, ScoredChunk
from app.providers.embeddings import EmbeddingProvider
from app.providers.llm import NO_ANSWER, LLMProvider, LLMResponse
from app.providers.vector_store import VectorStore
from app.rag.citations import CitationMapper
from app.rag.pipeline import RAGPipeline
from app.rag.prompt_builder import PromptBuilder
from app.rag.retriever import Retriever

MEASURED_UNANSWERABLE_TOP1 = 0.2115  # "Welchen Umsatz erzielte Apple im letzten Quartal?"
MEASURED_ANSWERABLE_MIN = 0.3913  # "Fuer wen wurde das System als Testprojekt entwickelt?"


class _StubEmbedder(EmbeddingProvider):
    @property
    def dimension(self) -> int:
        return 2

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class _FixedScoreStore(VectorStore):
    """Liefert immer einen Chunk mit festem Score — der Messwert wird eingespeist."""

    def __init__(self, score: float) -> None:
        self._score = score

    def upsert(self, chunks, vectors, namespace):  # pragma: no cover - nicht gebraucht
        raise NotImplementedError

    def query(self, vector, top_k, namespace):
        chunk = Chunk(
            id="c0", document_id="d0", document_name="doc.txt",
            chunk_index=0, page=1, text="Irgendein Quelltext.",
        )
        return [ScoredChunk(chunk=chunk, score=self._score)]

    def delete_document(self, document_id, namespace):  # pragma: no cover
        raise NotImplementedError


class _SpyLLM(LLMProvider):
    def __init__(self) -> None:
        self.calls = 0

    def complete(self, messages):
        self.calls += 1
        return LLMResponse(text="Antwort [1]")


def _pipeline(score: float, spy: _SpyLLM) -> RAGPipeline:
    retriever = Retriever(
        embedder=_StubEmbedder(),
        store=_FixedScoreStore(score),
        top_k=6,
        min_score=OPENAI_MIN_SCORE,
    )
    return RAGPipeline(
        retriever=retriever,
        prompt_builder=PromptBuilder(),
        llm=spy,
        citation_mapper=CitationMapper(),
    )


def test_below_threshold_yields_no_answer_without_llm_call():
    """Gemessener Score einer unbeantwortbaren Golden-Frage → Threshold greift."""
    spy = _SpyLLM()
    answer = _pipeline(MEASURED_UNANSWERABLE_TOP1, spy).answer(
        "Welchen Umsatz erzielte Apple im letzten Quartal?", "nb"
    )
    assert answer.text == NO_ANSWER
    assert answer.citations == []
    assert spy.calls == 0, "unter dem Threshold darf das LLM gar nicht erst laufen"


def test_above_threshold_reaches_the_llm():
    """Gemessener Minimal-Score einer beantwortbaren Golden-Frage → passiert den Filter."""
    spy = _SpyLLM()
    answer = _pipeline(MEASURED_ANSWERABLE_MIN, spy).answer(
        "Fuer wen wurde das System als Testprojekt entwickelt?", "nb"
    )
    assert spy.calls == 1
    assert answer.text != NO_ANSWER
    assert [c.n for c in answer.citations] == [1]


def test_settings_resolve_min_score_per_provider():
    assert Settings(providers="openai", min_score_override=None).min_score == 0.30
    assert Settings(providers="fake", min_score_override=None).min_score == 0.05
    assert Settings(providers="fake", min_score_override=0.42).min_score == 0.42
