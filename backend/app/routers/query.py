"""Query endpoint — the heart of the RAG app.

Flow:
1. Receive user's question
2. Hybrid retrieval (semantic + keyword)
3. Cross-encoder reranking
4. LLM generates answer with inline citations
5. Return answer + full citation details (for source viewer)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.routers.auth import get_current_user
from app.schemas.query import Citation, QueryRequest, QueryResponse
from app.services.llm import generate_answer
from app.services.reranker import rerank
from app.services.retrieval import hybrid_search

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_documents(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. Hybrid retrieval (top 20 candidates)
    candidates = hybrid_search(request.question, db, current_user.id, top_k=20)
    if not candidates:
        return QueryResponse(
            answer="I don't have enough information in the provided documents to answer that.",
            citations=[],
            query=request.question,
        )

    # 2. Rerank down to top_k
    top_chunks = rerank(request.question, candidates, top_k=request.top_k)
    if not top_chunks:
        return QueryResponse(
            answer="I don't have enough information in the provided documents to answer that.",
            citations=[],
            query=request.question,
        )

    # 3. LLM generates answer with inline citations
    try:
        answer = generate_answer(request.question, top_chunks)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {str(e)}",
        )

    # 4. Build citation objects (index matches the [1], [2] in the answer)
    citations = [
        Citation(
            index=i + 1,
            chunk_id=chunk.chunk_id,
            document_id=chunk.document_id,
            document_filename=chunk.document_filename,
            page_number=chunk.page_number,
            content=chunk.content,
            score=chunk.score,
        )
        for i, chunk in enumerate(top_chunks)
    ]

    return QueryResponse(
        answer=answer,
        citations=citations,
        query=request.question,
    ) 