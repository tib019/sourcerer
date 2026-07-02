"""Deterministische Retrieval-Mathematik: Cosine-Similarity + Top-k-Ranking.

Feste, von Hand nachrechenbare Vektoren — kein Embedding-Modell im Spiel.
"""

import math

import pytest

from app.domain import Chunk
from app.providers.vector_store import InMemoryVectorStore, cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_hand_computed_value(self):
        # a=(1,2), b=(3,4): dot=11, |a|=sqrt(5), |b|=5 → 11 / (5*sqrt(5))
        expected = 11 / (5 * math.sqrt(5))
        assert cosine_similarity([1.0, 2.0], [3.0, 4.0]) == pytest.approx(expected)

    def test_45_degrees(self):
        assert cosine_similarity([1.0, 0.0], [1.0, 1.0]) == pytest.approx(
            math.sqrt(2) / 2
        )

    def test_zero_vector_is_zero_not_nan(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_scale_invariance(self):
        a, b = [1.0, 2.0, 3.0], [4.0, 5.0, 6.0]
        scaled = [x * 42.0 for x in a]
        assert cosine_similarity(a, b) == pytest.approx(cosine_similarity(scaled, b))

    def test_dimension_mismatch_raises(self):
        with pytest.raises(ValueError):
            cosine_similarity([1.0], [1.0, 2.0])


def _chunk(i: int) -> Chunk:
    return Chunk(
        id=f"c{i}",
        document_id="d1",
        document_name="doc.txt",
        chunk_index=i,
        page=1,
        text=f"chunk {i}",
    )


class TestTopKRanking:
    def _store(self) -> InMemoryVectorStore:
        store = InMemoryVectorStore()
        # Bekannte Winkel zur Query (1,0):
        # c0: (1,0)   → cos = 1.0
        # c1: (1,1)   → cos ≈ 0.7071
        # c2: (0,1)   → cos = 0.0
        # c3: (2,1)   → cos = 2/sqrt(5) ≈ 0.8944
        store.upsert(
            [_chunk(0), _chunk(1), _chunk(2), _chunk(3)],
            [[1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [2.0, 1.0]],
            namespace="nb",
        )
        return store

    def test_ranking_order_is_exact(self):
        results = self._store().query([1.0, 0.0], top_k=4, namespace="nb")
        assert [r.chunk.id for r in results] == ["c0", "c3", "c1", "c2"]
        assert results[0].score == pytest.approx(1.0)
        assert results[1].score == pytest.approx(2 / math.sqrt(5))
        assert results[2].score == pytest.approx(math.sqrt(2) / 2)
        assert results[3].score == pytest.approx(0.0)

    def test_top_k_limits_results(self):
        assert len(self._store().query([1.0, 0.0], top_k=2, namespace="nb")) == 2

    def test_namespace_isolation(self):
        store = self._store()
        assert store.query([1.0, 0.0], top_k=4, namespace="anderes-notebook") == []

    def test_delete_document_removes_vectors(self):
        store = self._store()
        store.delete_document("d1", namespace="nb")
        assert store.query([1.0, 0.0], top_k=4, namespace="nb") == []
