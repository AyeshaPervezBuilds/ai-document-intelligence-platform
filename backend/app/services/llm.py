"""LLM integration via Groq.

The LLM's job in this app:
1. Read the user's question
2. Read the retrieved chunks (with their citation indices)
3. Generate an answer that is GROUNDED in the chunks
4. Cite sources inline using [1], [2], etc.

If the chunks don't contain the answer, the LLM must say so
— this prevents hallucination.
"""
from groq import Groq

from app.core.config import settings
from app.services.retrieval import RetrievedChunk


MODEL_NAME = "openai/gpt-oss-120b" 


SYSTEM_PROMPT = """You are a document question-answering assistant.

Your rules:
1. Answer ONLY using the provided context chunks.
2. Every factual claim must include an inline citation like [1] or [2],
   referring to the numbered context chunks.
3. If the answer is not present in the context, respond EXACTLY with:
   "I don't have enough information in the provided documents to answer that."
4. Be concise and precise. Do not add information from outside the context.
5. If multiple chunks support a claim, cite all of them: [1][3].
"""


def _build_context_block(chunks: list[RetrievedChunk]) -> str:
    """Format chunks into a numbered context block for the LLM."""
    lines = []
    for i, chunk in enumerate(chunks, start=1):
        page = f", page {chunk.page_number}" if chunk.page_number else ""
        lines.append(
            f"[{i}] Source: {chunk.document_filename}{page}\n"
            f"{chunk.content}\n"
        )
    return "\n".join(lines)


def generate_answer(
    query: str, chunks: list[RetrievedChunk]
) -> str:
    """Generate a citation-grounded answer from retrieved chunks.

    Args:
        query: user's question
        chunks: reranked chunks (each will be cited by its index+1)

    Returns:
        LLM-generated answer text with inline citations like [1], [2].
    """
    if not chunks:
        return "I don't have enough information in the provided documents to answer that."

    client = Groq(api_key=settings.groq_api_key)
    context = _build_context_block(chunks)

    user_message = (
        f"Context chunks:\n\n{context}\n\n"
        f"Question: {query}\n\n"
        f"Provide a grounded answer with inline citations."
    )

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.1,  # low temp for factual, consistent answers
        max_tokens=1024,
    )

    return response.choices[0].message.content or "" 