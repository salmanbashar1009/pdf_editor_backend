"""Tests for POST /api/translate-pdf."""

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_sample_pdf(text: str = "Hello World") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 50), text)
    data = doc.tobytes()
    doc.close()
    return data


def test_translate_valid_pdf_en_to_es():
    pdf_bytes = create_sample_pdf("The three fundamental principles")
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "es"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="translated_doc_en_to_es.pdf"' in response.headers.get("content-disposition", "")


def test_translate_valid_pdf_en_to_bn():
    pdf_bytes = create_sample_pdf("Good morning my friend")
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "bn"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_translate_missing_file():
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "es"},
    )
    assert response.status_code == 422


def test_translate_missing_source_language():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/api/translate-pdf",
        data={"target_language": "es"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_translate_missing_target_language():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_translate_unsupported_language_code():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "xyz"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_translate_same_source_and_target():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "en"},
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 400


def test_translate_corrupt_pdf():
    response = client.post(
        "/api/translate-pdf",
        data={"source_language": "en", "target_language": "es"},
        files={"file": ("bad.pdf", b"INVALID BYTES", "application/pdf")},
    )
    assert response.status_code == 400
