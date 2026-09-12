"""Integration tests for API health and OpenAPI documentation."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema.get("paths", {})
    assert "/api/translate-pdf" in paths
    assert "/editor/pdf/watermark" in paths
    assert "/health" in paths


def test_docs_page():
    response = client.get("/docs")
    assert response.status_code == 200
