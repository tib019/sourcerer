"""Empirische Kalibrierung des Retrieval-Mindest-Scores (ADR-004).

Misst auf dem Groundedness-Golden-Set die Top-1-Cosine-Scores:
- beantwortbare Fragen  -> Scores MUESSEN ueber dem Threshold bleiben
- unbeantwortbare Fragen -> Scores MUESSEN darunter liegen

Vorschlag = Mittelwert zwischen max(unbeantwortbar) und min(beantwortbar).

Aufruf:
    python scripts/calibrate_min_score.py            # Fake-Embeddings (offline)
    python scripts/calibrate_min_score.py openai     # echte OpenAI-Embeddings (braucht Key)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ingest.chunker import Chunker  # noqa: E402
from app.ingest.extractor import PlainTextExtractor  # noqa: E402
from app.providers.embeddings import FakeEmbeddings  # noqa: E402
from app.providers.vector_store import InMemoryVectorStore  # noqa: E402

EVAL_DIR = Path(__file__).parent.parent / "tests" / "eval"
GOLDEN = json.loads((EVAL_DIR / "golden_set.json").read_text(encoding="utf-8"))
DOCUMENT = (EVAL_DIR / "test_document.txt").read_bytes()


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "fake"
    if mode == "openai":
        from app.providers.embeddings import OpenAIEmbeddings

        embedder = OpenAIEmbeddings(api_key=os.environ["OPENAI_API_KEY"])
    else:
        embedder = FakeEmbeddings()

    store = InMemoryVectorStore()
    pages = PlainTextExtractor().extract(DOCUMENT)
    chunks = Chunker(chunk_size=60, overlap=10).chunk(
        pages, document_id="handbuch", document_name="handbuch.txt"
    )
    store.upsert(chunks, embedder.embed([c.text for c in chunks]), namespace="cal")

    def top1(question: str) -> float:
        vector = embedder.embed([question])[0]
        results = store.query(vector, top_k=1, namespace="cal")
        return results[0].score if results else 0.0

    answerable = [(c["question"], top1(c["question"])) for c in GOLDEN["answerable"]]
    unanswerable = [(c["question"], top1(c["question"])) for c in GOLDEN["unanswerable"]]

    print(f"== Provider: {mode} ==")
    print("-- beantwortbar (muss > Threshold) --")
    for question, score in answerable:
        print(f"  {score:.4f}  {question}")
    print("-- unbeantwortbar (muss <= Threshold) --")
    for question, score in unanswerable:
        print(f"  {score:.4f}  {question}")

    lo = max(score for _, score in unanswerable)
    hi = min(score for _, score in answerable)
    print(f"\nmax(unbeantwortbar) = {lo:.4f}")
    print(f"min(beantwortbar)   = {hi:.4f}")
    if lo >= hi:
        print("!! Keine saubere Trennung — Threshold allein reicht nicht, "
              "Prompt-Instruktion bleibt zweite Verteidigungslinie.")
    else:
        print(f"Vorschlag min_score = {(lo + hi) / 2:.2f} (Mitte, Marge beidseitig)")


if __name__ == "__main__":
    main()
