
import importlib

import faiss
import numpy as np

from app.config import EMBEDDING_MODEL


class EvidenceRetriever:
    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL,
        min_similarity: float = 0.0,
    ):
        if not -1.0 <= min_similarity <= 1.0:
            raise ValueError(
                "min_similarity must be between -1.0 and 1.0."
            )

        SentenceTransformer = importlib.import_module(
            "sentence_transformers"
        ).SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.index = None
        self.chunks = []
        self.min_similarity = min_similarity

    def build_index(self, chunks: list[dict]) -> None:
        if not chunks:
            raise ValueError(
                "Cannot index an empty document collection."
            )

        # Skip empty or unusable text instead of indexing it.
        valid_chunks = []
        for chunk in chunks:
            text = chunk.get("text", "")
            if isinstance(text, str) and text.strip():
                cleaned = dict(chunk)
                cleaned["text"] = text.strip()
                valid_chunks.append(cleaned)

        if not valid_chunks:
            raise ValueError(
                "No chunks with usable text were provided."
            )

        texts = [chunk["text"] for chunk in valid_chunks]

        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        )

        vectors = np.asarray(vectors, dtype=np.float32)

        if vectors.ndim != 2 or vectors.shape[0] != len(valid_chunks):
            raise ValueError(
                "Embedding vectors do not match the chunk collection."
            )

        if not np.isfinite(vectors).all():
            raise ValueError(
                "Embedding vectors contain invalid values."
            )

        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)
        self.chunks = valid_chunks

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

        if (
            query_vector.ndim != 2
            or query_vector.shape[0] != 1
            or query_vector.shape[1] != self.index.d
            or not np.isfinite(query_vector).all()
        ):
            raise ValueError("Invalid query embedding.")

        k = min(top_k, len(self.chunks))
        scores, indices = self.index.search(query_vector, k)

        results = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue

            score = float(score)

            # Exclude matches below the configured threshold.
            if score < getattr(self, "min_similarity", 0.0):
                continue

            result = dict(self.chunks[int(idx)])
            result["similarity"] = score
            results.append(result)

        return results
