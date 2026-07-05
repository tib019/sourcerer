"""Threshold-Pfad: der min_score ist ein Rausch-Floor, kein Relevanz-Urteil (ADR-004).

Hintergrund (Produktions-Incident, 2. Kalibrierung): echte Kurz-Queries auf ein echtes
Paper scoren niedrig — gemessen mit text-embedding-3-small gegen den Live-Index:
  "Ideologie"  top1 = 0.1236   (in-source, sinngemäß beantwortbar)
  "Stufe 1"    top1 = 0.2114   (in-source, cross-lingual: Quelle sagt "Stage 1")
  out-of-source Fragen scoren bis 0.2115
=> KEIN Skalarwert trennt beides. Der Threshold filtert nur noch Rauschen (0.05);
Groundedness entscheidet der Prompt. Diese Tests nageln beide Seiten fest.
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

MEASURED_TERSE_INSOURCE_TOP1 = 0.1236  # "Ideologie" gegen Cybersyn-Paper (Incident!)
NOISE_SCORE = 0.03  # unterhalb des Floors: kein inhaltlicher Zusammenhang


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

    def delete_namespace(self, namespace):  # pragma: no cover - nicht gebraucht
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


def test_noise_below_floor_yields_no_answer_without_llm_call():
    spy = _SpyLLM()
    answer = _pipeline(NOISE_SCORE, spy).answer("Voellig fremde Frage?", "nb")
    assert answer.text == NO_ANSWER
    assert answer.citations == []
    assert spy.calls == 0, "unter dem Floor darf das LLM gar nicht erst laufen"


def test_terse_insource_query_reaches_the_llm():
    """Incident-Regression: Kurz-Query mit gemessenem Score 0.1236 MUSS zum LLM.

    Genau dieser Fall lieferte in Produktion faelschlich NO_ANSWER, als der
    Threshold 0.30 betrug (gegen ein zu einfaches Golden-Set kalibriert).
    """
    spy = _SpyLLM()
    answer = _pipeline(MEASURED_TERSE_INSOURCE_TOP1, spy).answer("Ideologie", "nb")
    assert spy.calls == 1
    assert answer.text != NO_ANSWER
    assert [c.n for c in answer.citations] == [1]


def test_settings_resolve_min_score_per_provider():
    assert Settings(providers="openai", min_score_override=None).min_score == 0.05
    assert Settings(providers="fake", min_score_override=None).min_score == 0.05
    assert Settings(providers="fake", min_score_override=0.42).min_score == 0.42
