"""Integration tests for MediBot AI FastAPI endpoints."""
import os
import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)
SAMPLE_PDF_PATH = os.path.join("data", "uploaded_pdfs", "clinical_hypertension_diabetes_guide.pdf")


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "vector_store_ready" in data
    assert "total_documents" in data
    assert "groq_configured" in data


def test_api_chat_empty_question():
    response = client.post("/api/chat", json={"question": ""})
    assert response.status_code == 400


def test_api_chat_query():
    response = client.post(
        "/api/chat",
        json={
            "question": "What is hypertension and how is it managed?",
            "session_id": "integration-test-session"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert data["session_id"] == "integration-test-session"


def test_api_document_lifecycle():
    assert os.path.exists(SAMPLE_PDF_PATH), "Sample PDF should exist"
    
    with open(SAMPLE_PDF_PATH, "rb") as f:
        pdf_bytes = f.read()

    # 1. Upload Document
    upload_res = client.post(
        "/api/documents/upload",
        files={"file": ("test_upload_guide.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["status"] == "success"
    doc = upload_data["document"]
    doc_id = doc["document_id"]
    assert doc["filename"] == "test_upload_guide.pdf"
    assert doc["pages"] == 2
    assert doc["chunks"] >= 2

    # 2. Get Documents List
    list_res = client.get("/api/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert any(d["document_id"] == doc_id for d in list_data["documents"])

    # 3. Chat against newly indexed document
    chat_res = client.post(
        "/api/chat",
        json={
            "question": "What fasting plasma glucose level indicates diabetes?",
            "session_id": "test-doc-session"
        }
    )
    assert chat_res.status_code == 200
    chat_data = chat_res.json()
    assert len(chat_data["sources"]) > 0
    assert any("test_upload_guide.pdf" in s["source"] for s in chat_data["sources"])

    # 4. Check Session History
    hist_res = client.get("/api/sessions/test-doc-session/history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data["messages"]) >= 2

    # 5. Delete Document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["status"] == "success"

    # 6. Verify Document is gone from list
    list_after = client.get("/api/documents").json()
    assert not any(d["document_id"] == doc_id for d in list_after["documents"])

