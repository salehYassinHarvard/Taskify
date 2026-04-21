"""
PDF text extraction using PyMuPDF (fitz).

PyMuPDF is fast, handles most layouts well, and produces clean text
suitable for feeding to an LLM for syllabus parsing.
"""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF


def extract_text(pdf_bytes: bytes) -> str:
    """Extract all text from a PDF byte string."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        pages = [page.get_text("text") for page in doc]
        return "\n\n".join(pages)
    finally:
        doc.close()


def extract_text_from_path(path: str | Path) -> str:
    """Extract all text from a PDF on disk."""
    doc = fitz.open(str(path))
    try:
        pages = [page.get_text("text") for page in doc]
        return "\n\n".join(pages)
    finally:
        doc.close()


def extract_with_metadata(pdf_bytes: bytes) -> dict:
    """Return text plus basic metadata (title, page count)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        meta = doc.metadata or {}
        text = "\n\n".join(page.get_text("text") for page in doc)
        return {
            "text": text,
            "page_count": len(doc),
            "title": meta.get("title") or "",
            "author": meta.get("author") or "",
        }
    finally:
        doc.close()
