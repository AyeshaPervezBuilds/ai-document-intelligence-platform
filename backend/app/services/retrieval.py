"""Hybrid retrieval: semantic (pgvector) + keyword (BM25), then rerank.

Why hybrid?
- Semantic (embeddings): finds conceptually similar text, even with different words.
- Keyword (BM25): finds exact term matches, good for names, codes, rare terms.
- Combining both gives better recall than either alone.

Why rerank?
- Initial retrieval (top-20) is fast but coarse.
- A cross-encoder reranks the top results against the query for precision.
"""
from dataclasses import dataclass

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.embeddings import embed_query


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_filename: str
    chunk_index: int
    page_number: int | None
    content: str
    score: float
    source: str  # "semantic", "keyword", or "hybrid"


def semantic_search(
    query: str, db: Session, user_id, top_k: int = 20
) -> list[RetrievedChunk]:
    """Vector similarity search using pgvector's cosine distance."""
    query_vec = embed_query(query)

    # pgvector: use <=> operator (cosine distance). Lower = more similar.
    # We fetch top_k chunks owned by this user.
    stmt = (
        select(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id)
        .where(Chunk.embedding.isnot(None))
        .order_by(Chunk.embedding.cosine_distance(query_vec))
        .limit(top_k)
    )
    rows = db.execute(stmt).all()

    results: list[RetrievedChunk] = []
    for chunk, filename in rows:
        # cosine_distance = 1 - cosine_similarity, so similarity = 1 - distance
        # We'll compute a pseudo-score in [0, 1] for ranking.
        # (We can't access the distance directly here since we didn't select it.
        #  For simplicity, we use rank-order scores below.)
        results.append(
            RetrievedChunk(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                document_filename=filename,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                content=chunk.content,
                score=0.0,  # filled in below
                source="semantic",
            )
        )

    # Assign rank-based scores (higher = better)
    n = len(results)
    for i, r in enumerate(results):
        r.score = (n - i) / n if n else 0.0

    return results


def keyword_search(
    query: str, db: Session, user_id, top_k: int = 20
) -> list[RetrievedChunk]:
    """BM25 keyword search across user's chunks."""
    # Fetch all chunks for this user (in a real prod system, we'd use a proper
    # search index like Elasticsearch/OpenSearch; for a single-user portfolio
    # project, in-memory BM25 over the user's chunks is fine).
    stmt = (
        select(Chunk, Document.filename)
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id)
    )
    rows = db.execute(stmt).all()
    if not rows:
        return []

    tokenized_corpus = [c.content.lower().split() for c, _ in rows]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    # Get top_k indices
    indexed = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    results: list[RetrievedChunk] = []
    max_score = max((s for _, s in indexed), default=1.0) or 1.0
    for idx, score in indexed:
        if score <= 0:
            continue  # skip zero-score matches
        chunk, filename = rows[idx]
        results.append(
            RetrievedChunk(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                document_filename=filename,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                content=chunk.content,
                score=score / max_score,
                source="keyword",
            )
        )
    return results


def hybrid_search(
    query: str, db: Session, user_id, top_k: int = 20
) -> list[RetrievedChunk]:
    """Combine semantic and keyword results via Reciprocal Rank Fusion (RRF)."""
    semantic = semantic_search(query, db, user_id, top_k=top_k)
    keyword = keyword_search(query, db, user_id, top_k=top_k)

    # Reciprocal Rank Fusion: score = sum(1 / (k + rank))
    # k=60 is the standard constant from the RRF paper.
    RRF_K = 60
    merged: dict[str, RetrievedChunk] = {}
    fused_scores: dict[str, float] = {}

    for source_list in (semantic, keyword):
        for rank, item in enumerate(source_list):
            rrf_score = 1.0 / (RRF_K + rank + 1)
            if item.chunk_id not in merged:
                merged[item.chunk_id] = item
                fused_scores[item.chunk_id] = 0.0
            fused_scores[item.chunk_id] += rrf_score

    # Build final list
    results = []
    for chunk_id, item in merged.items():
        item.score = fused_scores[chunk_id]
        item.source = "hybrid"
        results.append(item)

    results.sort(key=lambda r: r.score, reverse=True)
    return results[:top_k] 