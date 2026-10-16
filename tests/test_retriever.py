
import numpy as np
import pytest

from app.retriever import EvidenceRetriever


class FakeEmbeddingModel:
    """Deterministic embeddings so tests don't need model downloads."""

    def encode(self, texts, **kwargs):
        vectors = {
            "information security policy": [1.0, 0.0, 0.0],
            "risk assessment process": [0.0, 1.0, 0.0],
            "incident response plan": [0.0, 0.0, 1.0],
        }
        return np.array(
            [vectors[text] for text in texts],
            dtype=np.float32,
        )


@pytest.fixture
def retriever():
    instance = EvidenceRetriever.__new__(EvidenceRetriever)
    instance.model = FakeEmbeddingModel()
    instance.index = None
    instance.chunks = []
    instance.build_index([
        {
            "source": "security.pdf",
            "page": 1,
            "chunk_id": 0,
            "text": "information security policy",
        },
        {
            "source": "security.pdf",
            "page": 2,
            "chunk_id": 1,
            "text": "risk assessment process",
        },
        {
            "source": "security.pdf",
            "page": 3,
            "chunk_id": 2,
            "text": "incident response plan",
        },
    ])
    return instance


def test_build_index_rejects_empty_chunks():
    instance = EvidenceRetriever.__new__(EvidenceRetriever)
    instance.model = FakeEmbeddingModel()
    instance.index = None
    instance.chunks = []

    with pytest.raises(ValueError, match="empty document collection"):
        instance.build_index([])


def test_search_returns_most_relevant_chunk(retriever):
    results = retriever.search("risk assessment process", top_k=2)

    assert len(results) == 2
    assert results[0]["chunk_id"] == 1
    assert results[0]["similarity"] == pytest.approx(1.0)


def test_search_preserves_metadata(retriever):
    results = retriever.search("information security policy")

    assert results[0]["source"] == "security.pdf"
    assert results[0]["page"] == 1
    assert results[0]["chunk_id"] == 0


def test_search_rejects_empty_question(retriever):
    with pytest.raises(ValueError, match="Question cannot be empty"):
        retriever.search("   ")


def test_search_rejects_non_positive_top_k(retriever):
    with pytest.raises(ValueError, match="top_k must be positive"):
        retriever.search("risk assessment process", top_k=0)


def test_search_requires_index():
    instance = EvidenceRetriever.__new__(EvidenceRetriever)
    instance.model = FakeEmbeddingModel()
    instance.index = None
    instance.chunks = []

    with pytest.raises(
        RuntimeError,
        match="Build the index before searching",
    ):
        instance.search("risk assessment process")

