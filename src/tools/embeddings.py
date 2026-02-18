"""Embedding utilities for novelty scoring.

Uses lightweight hash-based embeddings — sufficient for detecting
duplicate/similar short-form posts in novelty scoring.
"""

import hashlib
import math


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingClient:
    """Hash-based text embeddings for novelty scoring."""

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute deterministic embeddings from text content."""
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

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]


async def compute_novelty_score(
    candidate: str, recent_posts: list[str], client: EmbeddingClient | None = None
) -> float:
    """Compute novelty score (0-10) for a candidate post vs recent posts.

    Higher score = more novel/different from recent content.
    """
    if not recent_posts:
        return 8.0

    if client is None:
        client = EmbeddingClient()

    all_texts = [candidate] + recent_posts
    embeddings = client.embed_texts(all_texts)
    candidate_emb = embeddings[0]
    recent_embs = embeddings[1:]

    similarities = [cosine_similarity(candidate_emb, emb) for emb in recent_embs]
    avg_similarity = sum(similarities) / len(similarities)

    novelty = (1 - avg_similarity) * 10
    return max(0.0, min(10.0, novelty))
