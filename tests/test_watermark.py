"""Tests for POST /editor/pdf/watermark."""

import io
import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def create_sample_pdf(page_count: int = 1, text: str = "Sample Page Content") -> bytes:
    """Helper fixture to create a valid in-memory PDF with standard text."""
    doc = pymupdf.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((50, 50), f"{text} {i + 1}")
    data = doc.tobytes()
    doc.close()
    return data


def test_watermark_valid_single_page():
    pdf_bytes = create_sample_pdf(page_count=1)
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "CONFIDENTIAL",
            "position": "center",
            "opacity": "0.5",
            "color": "#FF0000",
        },
        files={"file": ("sample.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert 'filename="watermarked_sample.pdf"' in response.headers.get("content-disposition", "")

    # Re-open output PDF and verify watermark text is present on page
    out_doc = pymupdf.open(stream=response.content, filetype="pdf")
    assert len(out_doc) == 1
    page_text = out_doc[0].get_text()
    assert "CONFIDENTIAL" in page_text
    out_doc.close()


def test_watermark_multi_page_every_page():
    pdf_bytes = create_sample_pdf(page_count=3)
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "DRAFT 2026",
            "position": "bottom-right",
            "opacity": "0.8",
            "color": "#00FF00",
        },
        files={"file": ("multi.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200
    out_doc = pymupdf.open(stream=response.content, filetype="pdf")
    assert len(out_doc) == 3
    for page in out_doc:
        assert "DRAFT 2026" in page.get_text()
    out_doc.close()


@pytest.mark.parametrize(
    "pos",
    [
        "top-left",
        "top-center",
        "top-right",
        "center",
        "bottom-left",
        "bottom-center",
        "bottom-right",
    ],
)
def test_watermark_all_positions(pos):
    pdf_bytes = create_sample_pdf(page_count=1)
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "WATERMARK",
            "position": pos,
            "opacity": "0.5",
            "color": "#0000FF",
        },
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 200


def test_watermark_missing_file():
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "TEST",
            "position": "center",
            "opacity": "0.5",
            "color": "#123456",
        },
    )
    assert response.status_code == 422


def test_watermark_missing_text():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "position": "center",
            "opacity": "0.5",
            "color": "#123456",
        },
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_watermark_invalid_position():
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "TEST",
            "position": "middle-somewhere",
            "opacity": "0.5",
            "color": "#123456",
        },
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("bad_opacity", ["-0.1", "1.1", "invalid", "2.0"])
def test_watermark_invalid_opacity(bad_opacity):
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "TEST",
            "position": "center",
            "opacity": bad_opacity,
            "color": "#123456",
        },
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


@pytest.mark.parametrize("bad_color", ["123456", "#GGGGGG", "red", "#12345", "#1234567"])
def test_watermark_invalid_color(bad_color):
    pdf_bytes = create_sample_pdf()
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "TEST",
            "position": "center",
            "opacity": "0.5",
            "color": bad_color,
        },
        files={"file": ("doc.pdf", pdf_bytes, "application/pdf")},
    )
    assert response.status_code == 422


def test_watermark_malformed_pdf():
    response = client.post(
        "/editor/pdf/watermark",
        data={
            "text": "TEST",
            "position": "center",
            "opacity": "0.5",
            "color": "#123456",
        },
        files={"file": ("bad.pdf", b"NOT A VALID PDF CONTENT", "application/pdf")},
    )
    assert response.status_code == 400
