"""Text extraction from PDF, DOCX, and TXT files.

Each extractor returns a list of "pages" — each page has:
- page_number: 1-indexed page number (or None for formats without pages)
- text: the raw text content of that page
- char_start / char_end: position in the full concatenated text

Preserving page numbers is what enables citation-grounded answers later.
"""
from pathlib import Path
from typing import TypedDict

from docx import Document as DocxDocument
from pypdf import PdfReader


class ExtractedPage(TypedDict):
    page_number: int | None
    text: str
    char_start: int
    char_end: int


def extract_text(file_path: str, content_type: str) -> tuple[str, list[ExtractedPage]]:
    """Extract text from a document.

    Returns:
        (full_text, pages) where full_text is the concatenation of all pages,
        and pages is a list of ExtractedPage dicts with character offsets.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if content_type == "application/pdf":
        return _extract_pdf(path)
    elif content_type == "text/plain":
        return _extract_txt(path)
    elif content_type == (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return _extract_docx(path)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")


def _extract_pdf(path: Path) -> tuple[str, list[ExtractedPage]]:
    """Extract text from PDF, one entry per page."""
    reader = PdfReader(str(path))
    pages: list[ExtractedPage] = []
    full_parts: list[str] = []
    cursor = 0

    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if not text.strip():
            continue  # skip empty pages
        # add a page separator to keep chunks from bleeding across pages
        if full_parts:
            full_parts.append("\n\n")
            cursor += 2
        start = cursor
        full_parts.append(text)
        cursor += len(text)
        pages.append(
            ExtractedPage(
                page_number=i,
                text=text,
                char_start=start,
                char_end=cursor,
            )
        )

    return "".join(full_parts), pages


def _extract_txt(path: Path) -> tuple[str, list[ExtractedPage]]:
    """Extract text from plain text file (treated as a single page)."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    pages: list[ExtractedPage] = [
        ExtractedPage(
            page_number=None,
            text=text,
            char_start=0,
            char_end=len(text),
        )
    ]
    return text, pages


def _extract_docx(path: Path) -> tuple[str, list[ExtractedPage]]:
    """Extract text from DOCX. DOCX has no page concept, so treated as one page."""
    doc = DocxDocument(str(path))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    pages: list[ExtractedPage] = [
        ExtractedPage(
            page_number=None,
            text=text,
            char_start=0,
            char_end=len(text),
        )
    ]
    return text, pages  