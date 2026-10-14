"""Generate embeddings for text chunks using a local sentence-transformers model.

We use BAAI/bge-small-en-v1.5 — a small, fast, high-quality English model.
- 384-dimensional vectors
- Runs on CPU
- ~130 MB download (one time)
- No API key, no cost
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load and cache the embedding model (loaded once per process)."""
    return SentenceTransformer(MODEL_NAME)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns a list of 384-dim float vectors."""
    if not texts:
        return []
    model = get_model()
    vectors = model.encode(
        texts,
        normalize_embeddings=True,  # cosine similarity = dot product
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Embed a single query string.

    bge models recommend prefixing queries with this instruction for retrieval.
    """
    instruction = "Represent this sentence for searching relevant passages: "
    return embed_texts([instruction + query])[0] 