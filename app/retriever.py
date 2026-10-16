
import faiss
import importlib
import numpy as np

from app.config import EMBEDDING_MODEL


class EvidenceRetriever:
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        SentenceTransformer = importlib.import_module(
            "sentence_transformers"
        ).SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []

    def build_index(self, chunks: list[dict]) -> None:
        if not chunks:
            raise ValueError("Cannot index an empty document collection.")

        texts = [chunk["text"].strip() for chunk in chunks]

        if any(not text for text in texts):
            raise ValueError("Chunks must not contain empty text.")

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        vectors = np.asarray(vectors, dtype=np.float32)

        if not np.isfinite(vectors).all():
            raise ValueError("Embedding vectors contain invalid values.")

        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.chunks = chunks

    def search(
        self,
        question: str,
        top_k: int = 5,
    ) -> list[dict]:
        if self.index is None:
            raise RuntimeError("Build the index before searching.")

        if not question or not question.strip():
            raise ValueError("Question cannot be empty.")

        if top_k <= 0:
            raise ValueError("top_k must be positive.")

        query_vector = self.model.encode(
            [question.strip()],
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        query_vector = np.asarray(query_vector, dtype=np.float32)

        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_vector, k)

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            result = dict(self.chunks[int(idx)])
            result["similarity"] = float(score)
            results.append(result)

        return results
