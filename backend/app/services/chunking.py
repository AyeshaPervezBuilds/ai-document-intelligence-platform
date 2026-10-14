"""Chunk extracted text into overlapping pieces for embedding.

Design goals:
- Chunks should respect paragraph/sentence boundaries when possible.
- Every chunk must know which page it belongs to (for citations).
- Chunks should overlap slightly so context isn't lost at boundaries.

We use a simple but effective approach: split by paragraphs, then merge
adjacent paragraphs until we hit a target size. If a single paragraph is
too large, split it by sentences. If still too large, hard-split.
"""
import re
from typing import TypedDict

from app.services.extraction import ExtractedPage


class ChunkData(TypedDict):
    chunk_index: int
    content: str
    page_number: int | None
    char_start: int
    char_end: int


# Target size in characters (roughly ~500-800 tokens for English)
TARGET_CHUNK_SIZE = 1200
MIN_CHUNK_SIZE = 200
OVERLAP_SIZE = 150


def chunk_pages(pages: list[ExtractedPage]) -> list[ChunkData]:
    """Convert extracted pages into chunks with metadata preserved.

    Chunks never span across pages — this keeps page-level citations exact.
    """
    chunks: list[ChunkData] = []
    chunk_index = 0

    for page in pages:
        page_chunks = _chunk_text(page["text"], page["page_number"])
        for c in page_chunks:
            # offset within the full document
            offset_start = page["char_start"] + c["char_start"]
            offset_end = page["char_start"] + c["char_end"]
            chunks.append(
                ChunkData(
                    chunk_index=chunk_index,
                    content=c["content"],
                    page_number=page["page_number"],
                    char_start=offset_start,
                    char_end=offset_end,
                )
            )
            chunk_index += 1

    return chunks


def _chunk_text(text: str, page_number: int | None) -> list[dict]:
    """Split a single page's text into chunks.

    Returns list of dicts with keys: content, char_start, char_end
    """
    # Split into paragraphs (double newlines)
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paragraphs:
        return []

    chunks: list[dict] = []
    buffer: list[str] = []
    buffer_start = 0
    cursor = 0

    def flush():
        if not buffer:
            return
        content = "\n\n".join(buffer).strip()
        if not content:
            return
        chunks.append(
            {
                "content": content,
                "char_start": buffer_start,
                "char_end": buffer_start + len(content),
            }
        )

    for para in paragraphs:
        # locate paragraph in original text (approx — used only for offsets)
        para_pos = text.find(para, cursor)
        if para_pos == -1:
            para_pos = cursor
        cursor = para_pos + len(para)

        # if paragraph itself is too big, split it further
        if len(para) > TARGET_CHUNK_SIZE:
            flush()
            buffer = []
            for sub in _split_large_paragraph(para):
                chunks.append(
                    {
                        "content": sub,
                        "char_start": para_pos,
                        "char_end": para_pos + len(sub),
                    }
                )
            buffer_start = cursor
            continue

        # would adding this paragraph overflow the buffer?
        prospective = sum(len(p) for p in buffer) + len(buffer) * 2 + len(para)
        if prospective > TARGET_CHUNK_SIZE and buffer:
            flush()
            # start new buffer with slight overlap from previous chunk
            last_content = chunks[-1]["content"] if chunks else ""
            overlap = last_content[-OVERLAP_SIZE:] if last_content else ""
            buffer = [overlap, para] if overlap else [para]
            buffer_start = cursor - len(overlap)
        else:
            if not buffer:
                buffer_start = para_pos
            buffer.append(para)

    flush()
    return chunks


def _split_large_paragraph(paragraph: str) -> list[str]:
    """Split an oversized paragraph by sentence, then hard-split if needed."""
    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    parts: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 > TARGET_CHUNK_SIZE and current:
            parts.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        parts.append(current.strip())

    # hard-split anything still too large
    final: list[str] = []
    for part in parts:
        if len(part) <= TARGET_CHUNK_SIZE:
            final.append(part)
        else:
            for i in range(0, len(part), TARGET_CHUNK_SIZE):
                final.append(part[i : i + TARGET_CHUNK_SIZE])
    return final 