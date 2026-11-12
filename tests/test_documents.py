"""Tests for PDF document validation, text extraction, and chunking."""
import os
import pytest
from backend.document_processor import (
    validate_pdf_content,
    clean_text,
    process_pdf
)

SAMPLE_PDF_PATH = os.path.join("data", "uploaded_pdfs", "clinical_hypertension_diabetes_guide.pdf")


def test_validate_pdf_success():
    assert os.path.exists(SAMPLE_PDF_PATH), "Sample PDF should exist"
    with open(SAMPLE_PDF_PATH, "rb") as f:
        content = f.read()
    is_valid, err = validate_pdf_content(content, "guide.pdf")
    assert is_valid is True
    assert err == ""


def test_validate_pdf_invalid_extension():
    is_valid, err = validate_pdf_content(b"%PDF-1.4 sample", "medical_notes.txt")
    assert is_valid is False
    assert "Only PDF" in err


def test_validate_pdf_empty_file():
    is_valid, err = validate_pdf_content(b"", "empty.pdf")
    assert is_valid is False
    assert "empty" in err


def test_validate_pdf_corrupted_header():
    is_valid, err = validate_pdf_content(b"NOT_A_PDF_CONTENT", "corrupted.pdf")
    assert is_valid is False
    assert "%PDF-" in err


def test_clean_text():
    dirty = "Line 1 \r\n Line 2   \x00 with null and   spaces \n\n\n\n Line 3"
    cleaned = clean_text(dirty)
    assert "\x00" not in cleaned
    assert "   " not in cleaned
    assert "\n\n\n\n" not in cleaned
    assert "Line 1" in cleaned
    assert "Line 3" in cleaned


def test_process_pdf_chunking():
    with open(SAMPLE_PDF_PATH, "rb") as f:
        content = f.read()
    chunks, doc_info = process_pdf(content, "clinical_guide.pdf", document_id="test-doc-123")
    
    assert doc_info["document_id"] == "test-doc-123"
    assert doc_info["filename"] == "clinical_guide.pdf"
    assert doc_info["pages"] == 2
    assert doc_info["chunks"] >= 2
    assert len(chunks) == doc_info["chunks"]

    # Verify chunk structure and metadata preservation
    for chunk in chunks:
        assert "text" in chunk
        assert len(chunk["text"]) > 0
        meta = chunk["metadata"]
        assert meta["document_id"] == "test-doc-123"
        assert meta["source"] == "clinical_guide.pdf"
        assert meta["page"] in [1, 2]
        assert "chunk_id" in meta

