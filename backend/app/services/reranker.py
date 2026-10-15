"""Cross-encoder reranking for retrieved chunks.

Why rerank?
- Initial retrieval (semantic + BM25) is fast but coarse — it compares
  query and chunk *separately* (bi-encoder), losing fine-grained relevance.
- A cross-encoder reads the query and chunk *together* and scores their
  relevance jointly. Much more accurate, but too slow to run over the
  whole corpus.
- Solution: retrieve top-N (e.g., 20) with hybrid search, then rerank to
  pick top-K (e.g., 5) to send to the LLM.

Model: BAAI/bge-reranker-base — 278M params, free, runs on CPU.
"""
from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.services.retrieval import RetrievedChunk


MODEL_NAME = "BAAI/bge-reranker-base"


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load and cache the reranker model."""
    return CrossEncoder(MODEL_NAME)


def rerank(
    query: str,
    chunks: list[RetrievedChunk],
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Rerank chunks by cross-encoder relevance to the query.

    Args:
        query: user's question
        chunks: candidate chunks from hybrid retrieval
        top_k: how many to keep after reranking

    Returns:
        Top-k chunks sorted by cross-encoder score, each with `.score`
        updated to a normalized value in [0, 1].
    """
    if not chunks:
        return []

    model = get_reranker()

    # Build (query, passage) pairs
    pairs = [(query, c.content) for c in chunks]

    # Get raw scores (logits — can be negative, unbounded)
    raw_scores = model.predict(pairs, show_progress_bar=False)

    # Attach scores to chunks
    scored = list(zip(chunks, raw_scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    # Take top_k and normalize scores via softmax for display
    top = scored[:top_k]
    if not top:
        return []

    max_score = max(s for _, s in top)
    # Softmax-like normalization
    import math

    exp_scores = [math.exp(s - max_score) for _, s in top]
    total = sum(exp_scores) or 1.0

    results: list[RetrievedChunk] = []
    for (chunk, _raw), exp_s in zip(top, exp_scores):
        chunk.score = exp_s / total
        chunk.source = "reranked"
        results.append(chunk)
    return results 