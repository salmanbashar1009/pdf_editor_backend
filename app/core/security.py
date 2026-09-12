"""Untrusted-upload handling: size guard, magic bytes, structural validation."""

import logging
import re
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

import pymupdf

from app.core.exceptions import FileTooLarge, InvalidPDFFile

logger = logging.getLogger("pdf_editor")

PDF_MAGIC = b"%PDF-"
_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    """Reduce a user-supplied filename to a safe basename for response headers."""
    base = Path(name).name
    base = _SAFE_NAME_RE.sub("_", base).strip("._") or "document"
    return base[:120]


def read_upload(file, max_size: int) -> bytes:
    data = file.file.read(max_size + 1)
    if len(data) > max_size:
        raise FileTooLarge(f"File exceeds the maximum allowed size of {max_size} bytes")
    if not data:
        raise InvalidPDFFile("Uploaded file is empty")
    return data


def validate_pdf_bytes(data: bytes) -> None:
    """Reject non-PDFs and corrupt PDFs using structure, not just MIME type."""
    if not data.startswith(PDF_MAGIC):
        raise InvalidPDFFile("File is not a valid PDF")
    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise InvalidPDFFile("Malformed or unreadable PDF") from exc
    try:
        if doc.page_count == 0:
            raise InvalidPDFFile("PDF contains no pages")
    finally:
        doc.close()


@contextmanager
def temp_pdf_file(data: bytes):
    """Write bytes to a random name in a dedicated temp dir; always cleaned up."""
    tmpdir = Path(tempfile.mkdtemp(prefix="pdf_editor_"))
    path = tmpdir / f"{uuid.uuid4().hex}.pdf"
    try:
        path.write_bytes(data)
        yield path
    finally:
        for child in tmpdir.glob("*"):
            child.unlink(missing_ok=True)
        tmpdir.rmdir()