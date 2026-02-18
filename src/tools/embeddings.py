"""Embedding utilities for novelty scoring."""

import hashlib
import math

import httpx


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingClient:
    """Wrapper for computing text embeddings."""

    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self._mock = True  # Will be set to False when OpenAI key is available

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Compute embeddings for a list of texts."""
        if self._mock:
            return self._mock_embed(texts)
        return await self._real_embed(texts)

    async def embed_text(self, text: str) -> list[float]:
        results = await self.embed_texts([text])
        return results[0]

    def _mock_embed(self, texts: list[str]) -> list[list[float]]:
        """Simple hash-based mock embeddings for development."""
        embeddings = []
        for text in texts:
            h = hashlib.sha256(text.encode()).hexdigest()
            vec = [int(h[i : i + 2], 16) / 255.0 for i in range(0, min(len(h), 64), 2)]
            # Pad to 32 dimensions
            vec = (vec + [0.0] * 32)[:32]
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings

    async def _real_embed(self, texts: list[str]) -> list[list[float]]:
        """Real embeddings via OpenAI API."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._openai_key}"},
                json={"input": texts, "model": self.model},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]


async def compute_novelty_score(
    candidate: str, recent_posts: list[str], client: EmbeddingClient | None = None
) -> float:
    """Compute novelty score (0-10) for a candidate post vs recent posts.

    Higher score = more novel/different from recent content.
    """
    if not recent_posts:
        return 8.0  # High novelty if no history

    if client is None:
        client = EmbeddingClient()

    all_texts = [candidate] + recent_posts
    embeddings = await client.embed_texts(all_texts)
    candidate_emb = embeddings[0]
    recent_embs = embeddings[1:]

    similarities = [cosine_similarity(candidate_emb, emb) for emb in recent_embs]
    avg_similarity = sum(similarities) / len(similarities)

    novelty = (1 - avg_similarity) * 10
    return max(0.0, min(10.0, novelty))
