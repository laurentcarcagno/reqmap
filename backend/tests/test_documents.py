"""Tests for document upload, list, and node endpoints."""

import io
import json
import pytest
from unittest.mock import AsyncMock, patch


@pytest.fixture
def pdf_bytes():
    """Minimal valid-ish PDF bytes for upload testing."""
    return b"%PDF-1.4 fake pdf content for testing"


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf(client):
    data = {"customer": "airbus"}
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    response = await client.post("/api/v1/documents", data=data, files=files)
    assert response.status_code == 422
    assert "Unsupported file type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_upload_rejects_unknown_customer(client, tmp_path, monkeypatch):
    monkeypatch.setenv("CUSTOMERS_CONFIG_PATH", str(tmp_path / "customers.json"))
    (tmp_path / "customers.json").write_text(
        json.dumps({"customers": {"airbus": {"label": "Airbus", "req_id_pattern": "x", "noise_patterns": []}}}),
        encoding="utf-8",
    )
    from app.services import customer_config
    customer_config.load_customers_config.cache_clear()

    data = {"customer": "unknown_corp"}
    files = {"file": ("test.pdf", io.BytesIO(b"%PDF fake"), "application/pdf")}
    response = await client.post("/api/v1/documents", data=data, files=files)
    assert response.status_code == 422
    assert "Unknown customer" in response.json()["detail"]


@pytest.mark.asyncio
async def test_list_documents_empty(client):
    response = await client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_document_not_found(client):
    response = await client.get("/api/v1/documents/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_nodes_document_not_found(client):
    response = await client.get("/api/v1/documents/nonexistent-id/nodes")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_node_not_found(client):
    response = await client.patch(
        "/api/v1/nodes/nonexistent-id",
        json={"applicability": "A", "conformity": "C"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_node_invalid_applicability(client):
    response = await client.patch(
        "/api/v1/nodes/some-id",
        json={"applicability": "INVALID"},
    )
    assert response.status_code == 422
