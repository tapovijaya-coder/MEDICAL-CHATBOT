"""Tests for RAG pipeline, FAISS vector store, embeddings, and prompt generation."""
import os
import shutil
import pytest
from backend.embeddings import get_embedding_manager
from backend.vectorstore import FAISSStore
from backend.prompt_template import detect_emergency, build_rag_prompt
from backend.chatbot import SessionMemoryManager

TEST_VECTOR_DIR = os.path.join("tests", "test_vectorstore")


@pytest.fixture(autouse=True)
def cleanup_test_vectorstore():
    """Ensure a clean test directory before and after tests."""
    if os.path.exists(TEST_VECTOR_DIR):
        shutil.rmtree(TEST_VECTOR_DIR, ignore_errors=True)
    yield
    if os.path.exists(TEST_VECTOR_DIR):
        shutil.rmtree(TEST_VECTOR_DIR, ignore_errors=True)


def test_embedding_generation():
    manager = get_embedding_manager()
    assert manager.dimension == 384
    
    docs = ["Hypertension treatment protocol", "Diabetes diagnostic threshold"]
    vectors = manager.embed_documents(docs)
    assert len(vectors) == 2
    assert len(vectors[0]) == 384
    
    query_vec = manager.embed_query("blood pressure guidelines")
    assert len(query_vec) == 384


def test_faiss_vectorstore_add_search_delete():
    store = FAISSStore(storage_dir=TEST_VECTOR_DIR)
    assert store.total_documents == 0
    assert store.total_chunks == 0

    chunks = [
        {
            "text": "Hypertension is defined as blood pressure >= 130/80 mmHg.",
            "metadata": {"document_id": "doc-1", "source": "cardio.pdf", "page": 1, "chunk_id": "c1"}
        },
        {
            "text": "Type 2 diabetes diagnostic criteria include fasting plasma glucose >= 126 mg/dL.",
            "metadata": {"document_id": "doc-2", "source": "endo.pdf", "page": 1, "chunk_id": "c2"}
        }
    ]

    doc1_info = {"document_id": "doc-1", "filename": "cardio.pdf", "pages": 1, "chunks": 1, "file_size_bytes": 500}
    doc2_info = {"document_id": "doc-2", "filename": "endo.pdf", "pages": 1, "chunks": 1, "file_size_bytes": 600}

    store.add_document([chunks[0]], doc1_info)
    store.add_document([chunks[1]], doc2_info)

    assert store.total_documents == 2
    assert store.total_chunks == 2

    # Similarity search test
    results = store.similarity_search("What blood pressure indicates hypertension?", top_k=2)
    assert len(results) > 0
    assert results[0]["source"] == "cardio.pdf"
    assert "Hypertension is defined" in results[0]["text"]

    # Delete doc-1
    deleted = store.delete_document("doc-1")
    assert deleted is True
    assert store.total_documents == 1
    assert store.total_chunks == 1

    # Search again - should now only find doc-2
    results_after = store.similarity_search("What is hypertension?", top_k=2)
    for r in results_after:
        assert r["source"] != "cardio.pdf"


def test_detect_emergency():
    assert detect_emergency("I have crushing chest pain and feel dizzy") is True
    assert detect_emergency("Patient is having shortness of breath and slurred speech") is True
    assert detect_emergency("Severe allergic reaction with throat swelling") is True
    assert detect_emergency("What are the recommended dietary habits for mild hypertension?") is False
    assert detect_emergency("Can exercise lower systolic blood pressure?") is False


def test_build_rag_prompt():
    chunks = [
        {"source": "test.pdf", "page": 3, "text": "Metformin reduces hepatic glucose production."}
    ]
    history = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi, I am MediBot."}]
    prompt = build_rag_prompt("What does metformin do?", chunks, history)

    assert "Metformin reduces hepatic glucose production" in prompt
    assert "test.pdf" in prompt
    assert "Page: 3" in prompt
    assert "What does metformin do?" in prompt


def test_session_memory():
    memory = SessionMemoryManager(max_history_turns=5)
    sid = "test-session"
    
    memory.add_user_message(sid, "What is asthma?")
    memory.add_ai_message(sid, "Asthma is a chronic respiratory condition.")
    
    history = memory.get_history(sid)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    
    memory.clear_session(sid)
    assert len(memory.get_history(sid)) == 0

