"""Document ingestion: parse txt/docx/pdf into raw text."""
from __future__ import annotations

from pathlib import Path

SOURCE_TYPE_BY_EXT = {".txt": "paste", ".md": "paste", ".docx": "word", ".pdf": "pdf"}


def parse_txt(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def parse_docx(path: str | Path) -> str:
    from docx import Document

    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def parse_pdf(path: str | Path) -> str:
    from PyPDF2 import PdfReader

    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def source_type_for(path: str | Path) -> str:
    ext = Path(path).suffix.lower()
    if ext not in SOURCE_TYPE_BY_EXT:
        raise ValueError(f"Unsupported file extension: {ext}")
    return SOURCE_TYPE_BY_EXT[ext]


def parse_document(path: str | Path) -> str:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    ext = path.suffix.lower()
    if ext in (".txt", ".md"):
        return parse_txt(path)
    if ext == ".docx":
        return parse_docx(path)
    if ext == ".pdf":
        return parse_pdf(path)
    raise ValueError(f"Unsupported file extension: {ext}")
