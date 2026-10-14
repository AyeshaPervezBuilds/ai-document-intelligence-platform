"""Document ingestion pipeline.

Flow:
1. Extract text from the file (with page metadata)
2. Chunk the text (preserving page numbers)
3. Generate embeddings for each chunk
4. Save chunks to the database
5. Update the document status

This runs synchronously in the background after upload. For production we'd
move this to a proper task queue (Celery/RQ), but for now this is fine.
"""
import logging

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunking import chunk_pages
from app.services.embeddings import embed_texts
from app.services.extraction import extract_text

logger = logging.getLogger(__name__)


def ingest_document(document_id, db: Session) -> None:
    """Run the full ingestion pipeline for a document.

    Updates the document's status to 'processing' → 'ready' or 'failed'.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        logger.error(f"Document {document_id} not found")
        return

    try:
        document.status = "processing"
        db.commit()

        # 1. Extract
        logger.info(f"Extracting text from {document.filename}")
        full_text, pages = extract_text(document.file_path, document.content_type or "")
        if not full_text.strip():
            raise ValueError("No extractable text found in document")

        # 2. Chunk
        logger.info(f"Chunking {len(pages)} page(s)")
        chunks = chunk_pages(pages)
        if not chunks:
            raise ValueError("Chunking produced no chunks")
        logger.info(f"Produced {len(chunks)} chunks")

        # 3. Embed (batch for efficiency)
        logger.info("Generating embeddings...")
        texts = [c["content"] for c in chunks]
        vectors = embed_texts(texts)

        # 4. Save
        logger.info("Saving chunks to database...")
        # clear any prior chunks (in case of re-ingestion)
        db.query(Chunk).filter(Chunk.document_id == document.id).delete()
        for c, vec in zip(chunks, vectors):
            db.add(
                Chunk(
                    document_id=document.id,
                    chunk_index=c["chunk_index"],
                    content=c["content"],
                    page_number=c["page_number"],
                    char_start=c["char_start"],
                    char_end=c["char_end"],
                    embedding=vec,
                )
            )
        document.status = "ready"
        db.commit()
        logger.info(f"Ingestion complete for {document.id}")

    except Exception as e:
        logger.exception(f"Ingestion failed for {document_id}: {e}")
        document.status = "failed"
        db.commit() 