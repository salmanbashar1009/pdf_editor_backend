"""Extract plain text per page with PyMuPDF."""

import pymupdf


def extract_pages(pdf_bytes: bytes) -> list[str]:
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    try:
        return [page.get_text("text") for page in doc]
    finally:
        doc.close()