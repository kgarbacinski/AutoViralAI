"""Embedding utilities for novelty scoring.

Uses lightweight hash-based embeddings — detects exact duplicate content only;
swap in a real embedding model for semantic similarity.
"""

import hashlib
import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        raise ValueError(f"Vector length mismatch: {len(a)} vs {len(b)}")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingClient:
    """Hash-based text embeddings for novelty scoring.

    The interface is async-ready so swapping in a real embedding API
    (OpenAI, Cohere, etc.) only requires changing the implementation.
    """

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute deterministic embeddings from text content."""
        return self._embed_texts_sync(texts)

    async def embed_text(self, text: str) -> list[float]:
        result = await self.embed_texts([text])
        return result[0]

    @staticmethod
    def _embed_texts_sync(texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode()).hexdigest()
            vec = [int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), 64), 2)]
            vec = (vec + [0.0] * 32)[:32]
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings
