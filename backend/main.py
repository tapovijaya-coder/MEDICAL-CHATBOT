"""FastAPI REST API Server for MediBot AI."""
import os
import uuid
import shutil
import logging
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

from backend.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentInfo,
    DocumentListResponse,
    UploadResponse,
    HealthResponse,
    EvaluationItem,
    EvaluationReviewRequest,
    EvaluationReviewResponse
)
from backend.document_processor import validate_pdf_content, process_pdf
from backend.vectorstore import get_vector_store
from backend.chatbot import get_rag_engine
from backend.medical_dataset_manager import get_dataset_manager
from backend.medical_extractor import MEDICAL_CATEGORIES

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("medibot.api")

DATA_DIR = os.getenv("DATA_DIR", "data/uploaded_pdfs")
os.makedirs(DATA_DIR, exist_ok=True)

app = FastAPI(
    title="MediBot AI - Medical RAG Assistant API",
    description="Production-grade API for AI-assisted medical question answering using FAISS and Groq LLMs.",
    version="1.0.0"
)

# CORS configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
allowed_origins = [orig.strip() for orig in allowed_origins_env.split(",") if orig.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Returns health status, vector store document counts, chunk counts, and Groq configuration status."""
    vector_store = get_vector_store()
    rag_engine = get_rag_engine()
    
    return HealthResponse(
        status="healthy",
        vector_store_ready=vector_store.index is not None,
        total_documents=vector_store.total_documents,
        total_chunks=vector_store.total_chunks,
        groq_configured=bool(rag_engine.client is not None),
        embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        version="2.0.0",
        categories=MEDICAL_CATEGORIES
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """Answers a medical query using retrieved context from uploaded PDFs and Groq LLM."""
    if not request.question.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty."
        )
    
    rag_engine = get_rag_engine()
    try:
        response = rag_engine.query(
            question=request.question,
            session_id=request.session_id,
            category_filter=request.category_filter
        )
        return response
    except Exception as e:
        logger.error(f"Error answering chat query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while generating response: {str(e)}"
        )


@app.post("/api/documents/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Uploads, validates, extracts text, chunks, embeds, and indexes a medical PDF document."""
    filename = file.filename or "unknown.pdf"
    
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file stream."
        )

    # 1. Validate PDF file
    is_valid, error_msg = validate_pdf_content(file_bytes, filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    document_id = str(uuid.uuid4())

    # 2. Save physical file to disk
    local_file_path = os.path.join(DATA_DIR, f"{document_id}_{filename}")
    try:
        with open(local_file_path, "wb") as f:
            f.write(file_bytes)
    except Exception as e:
        logger.error(f"Failed to persist file to disk: {e}")

    # 3. Process PDF (extract text and chunk)
    try:
        chunks, doc_info = process_pdf(file_bytes, filename, document_id=document_id)
    except Exception as e:
        logger.error(f"Error processing PDF '{filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Failed to extract text or process PDF: {str(e)}"
        )

    # 4. Add to Vector Store
    vector_store = get_vector_store()
    try:
        vector_store.add_document(chunks, doc_info)
    except Exception as e:
        logger.error(f"Failed to index document in vector store: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document into vector store: {str(e)}"
        )

    saved_doc = vector_store.get_document(document_id) or doc_info

    doc_response = DocumentInfo(
        document_id=saved_doc["document_id"],
        filename=saved_doc["filename"],
        pages=saved_doc["pages"],
        chunks=saved_doc["chunks"],
        upload_date=saved_doc.get("upload_date", ""),
        file_size_bytes=saved_doc.get("file_size_bytes", len(file_bytes))
    )

    return UploadResponse(
        status="success",
        message=f"Document '{filename}' successfully processed and indexed ({doc_info['chunks']} chunks).",
        document=doc_response
    )


@app.get("/api/documents", response_model=DocumentListResponse, tags=["Documents"])
async def get_documents():
    """Returns metadata for all uploaded and indexed medical documents."""
    vector_store = get_vector_store()
    docs = vector_store.get_all_documents()
    
    total_pages = 0
    total_chunks = 0
    categories_breakdown: Dict[str, int] = {}
    
    # Calculate category statistics across all chunks
    for chunk in vector_store.chunks:
        cat = chunk.get("medical_category", "General Medicine")
        categories_breakdown[cat] = categories_breakdown.get(cat, 0) + 1

    document_items = []
    for d in docs:
        pages = d.get("pages", 0)
        chunks = d.get("chunks", 0)
        total_pages += pages
        total_chunks += chunks
        document_items.append(
            DocumentInfo(
                document_id=d["document_id"],
                filename=d["filename"],
                pages=pages,
                chunks=chunks,
                upload_date=d.get("upload_date", ""),
                file_size_bytes=d.get("file_size_bytes", 0),
                edition=d.get("edition", "Standard Reference"),
                publication_year=d.get("publication_year"),
                source_type=d.get("source_type", "medical_reference"),
                is_historical=d.get("is_historical", False),
                medical_categories=d.get("medical_categories", [])
            )
        )
    
    return DocumentListResponse(
        documents=document_items,
        total_documents=len(document_items),
        total_chunks=vector_store.total_chunks,
        total_pages=total_pages,
        categories_breakdown=categories_breakdown
    )


@app.get("/api/categories", tags=["Knowledge Base"])
async def get_categories():
    """Returns the list of 16 medical categories and chunk distribution counts."""
    vector_store = get_vector_store()
    counts: Dict[str, int] = {cat: 0 for cat in MEDICAL_CATEGORIES}
    
    for chunk in vector_store.chunks:
        cat = chunk.get("medical_category", "General Medicine")
        if cat in counts:
            counts[cat] += 1
        else:
            counts["General Medicine"] = counts.get("General Medicine", 0) + 1
            
    return {
        "categories": MEDICAL_CATEGORIES,
        "counts": counts,
        "total_chunks": vector_store.total_chunks
    }


@app.get("/api/evaluation/dataset", tags=["Evaluation"])
async def get_evaluation_dataset(
    difficulty: Optional[str] = None, 
    review_status: Optional[str] = None
):
    """Retrieves benchmark medical Q&A evaluation items with optional difficulty or review status filter."""
    dataset_mgr = get_dataset_manager()
    items = dataset_mgr.get_dataset(difficulty=difficulty, review_status=review_status)
    return {
        "total_items": len(items),
        "items": items
    }


@app.post("/api/evaluation/review", response_model=EvaluationReviewResponse, tags=["Evaluation"])
async def review_evaluation_item(review: EvaluationReviewRequest):
    """Allows a medical administrator to approve, reject, or annotate an evaluation benchmark item."""
    if review.review_status not in ["approved", "rejected", "pending"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review status must be 'approved', 'rejected', or 'pending'."
        )
    
    dataset_mgr = get_dataset_manager()
    success = dataset_mgr.update_item_review(review.id, review.review_status, review.expert_notes)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation item with ID '{review.id}' not found."
        )
        
    return EvaluationReviewResponse(
        status="success",
        message=f"Evaluation item '{review.id}' updated to status '{review.review_status}'.",
        item_id=review.id,
        new_status=review.review_status
    )


@app.get("/api/evaluation/report", tags=["Evaluation"])
async def get_evaluation_report():
    """Returns the medical knowledge quality report, conflict log, and RAG evaluation metrics."""
    dataset_mgr = get_dataset_manager()
    vector_store = get_vector_store()
    rag_engine = get_rag_engine()
    
    quality_report = dataset_mgr.get_quality_report()
    rag_eval = dataset_mgr.run_rag_evaluation(vector_store, rag_engine)
    
    return {
        "status": "success",
        "knowledge_quality_audit": quality_report,
        "rag_performance_evaluation": rag_eval
    }


@app.post("/api/evaluation/run", tags=["Evaluation"])
async def run_evaluation():
    """Triggers an active evaluation run measuring retrieval precision, recall, and citation accuracy."""
    dataset_mgr = get_dataset_manager()
    vector_store = get_vector_store()
    rag_engine = get_rag_engine()
    
    eval_result = dataset_mgr.run_rag_evaluation(vector_store, rag_engine)
    return {
        "status": "success",
        "result": eval_result
    }


@app.delete("/api/documents/{document_id}", tags=["Documents"])
async def delete_document(document_id: str):
    """Deletes a document from the vector store and removes its chunks from FAISS."""
    vector_store = get_vector_store()
    doc = vector_store.get_document(document_id)
    
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID '{document_id}' not found."
        )
    
    filename = doc.get("filename", "")
    success = vector_store.delete_document(document_id)
    
    # Remove file from disk if present
    for fname in os.listdir(DATA_DIR):
        if fname.startswith(f"{document_id}_"):
            try:
                os.remove(os.path.join(DATA_DIR, fname))
            except Exception as e:
                logger.warning(f"Could not delete physical file: {e}")
                
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove document from vector store."
        )
        
    return {
        "status": "success",
        "message": f"Document '{filename}' and all its vector embeddings were removed."
    }


@app.get("/api/sessions/{session_id}/history", tags=["Chat"])
async def get_session_history(session_id: str):
    """Retrieves conversation history for a specific session."""
    rag_engine = get_rag_engine()
    history = rag_engine.memory.get_history(session_id)
    return {"session_id": session_id, "messages": history}


@app.delete("/api/sessions/{session_id}", tags=["Chat"])
async def clear_session_history(session_id: str):
    """Clears conversation history for a given session."""
    rag_engine = get_rag_engine()
    rag_engine.memory.clear_session(session_id)
    return {"status": "success", "message": f"Session '{session_id}' cleared."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    uvicorn.run("backend.main:app", host=host, port=port, reload=True)

