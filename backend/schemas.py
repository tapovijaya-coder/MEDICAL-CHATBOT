"""Pydantic schemas for MediBot AI API request/response models."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(..., description="The medical query from the user", min_length=1)
    session_id: Optional[str] = Field(None, description="Unique conversation session ID")
    category_filter: Optional[str] = Field(None, description="Optional medical category filter")


class SourceCitation(BaseModel):
    source: str = Field(..., description="Name of the source document")
    page: Optional[int] = Field(None, description="Page number in the PDF (1-indexed)")
    excerpt: Optional[str] = Field(None, description="Relevant contextual snippet from the source")
    edition: Optional[str] = Field(None, description="Edition of the medical reference")
    publication_year: Optional[int] = Field(None, description="Publication year")
    medical_category: Optional[str] = Field(None, description="Medical taxonomy category")
    section_title: Optional[str] = Field(None, description="Extracted heading or topic section")
    source_type: Optional[str] = Field("medical_reference_book", description="Type of reference source")
    is_historical: bool = Field(False, description="Flag indicating if the publication is historical (< 2015)")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer from the medical assistant")
    sources: List[SourceCitation] = Field(default_factory=list, description="Citations from retrieved documents")
    session_id: str = Field(..., description="Active session ID for the conversation")
    is_emergency: bool = Field(default=False, description="Whether potential emergency symptoms were detected")
    has_historical_sources: bool = Field(default=False, description="Whether historical references were cited")
    medical_categories: List[str] = Field(default_factory=list, description="Matched clinical categories")


class DocumentInfo(BaseModel):
    document_id: str = Field(..., description="Unique ID of the uploaded document")
    filename: str = Field(..., description="Original filename of the PDF")
    pages: int = Field(..., description="Total pages in the PDF")
    chunks: int = Field(..., description="Number of text chunks indexed in the vector store")
    upload_date: str = Field(..., description="ISO formatted timestamp of upload")
    file_size_bytes: int = Field(..., description="Size of file in bytes")
    edition: Optional[str] = Field("Standard Edition", description="Edition identifier")
    publication_year: Optional[int] = Field(None, description="Publication year")
    source_type: Optional[str] = Field("medical_reference", description="Source type")
    is_historical: bool = Field(False, description="Whether marked as historical reference")
    medical_categories: List[str] = Field(default_factory=list, description="Categorical breakdown")


class DocumentListResponse(BaseModel):
    documents: List[DocumentInfo] = Field(default_factory=list)
    total_documents: int = Field(0)
    total_chunks: int = Field(0)
    total_pages: int = Field(0)
    categories_breakdown: Dict[str, int] = Field(default_factory=dict)


class UploadResponse(BaseModel):
    status: str
    message: str
    document: DocumentInfo
    extraction_report: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    vector_store_ready: bool
    total_documents: int
    total_chunks: int
    groq_configured: bool
    embedding_model: str
    version: str = "2.0.0"
    categories: List[str] = Field(default_factory=list)


class MessageHistoryItem(BaseModel):
    role: str
    content: str
    sources: Optional[List[SourceCitation]] = None
    timestamp: Optional[str] = None
    is_emergency: Optional[bool] = False
    has_historical_sources: Optional[bool] = False


class EvaluationItem(BaseModel):
    id: str
    difficulty: str
    question: str
    expected_answer: str
    supporting_document: str
    page_number: int
    medical_category: str
    evidence_status: str
    publication_year: int
    requires_expert_review: bool = False
    review_status: str = "pending"
    expert_notes: Optional[str] = None


class EvaluationReviewRequest(BaseModel):
    id: str = Field(..., description="Evaluation benchmark item ID")
    review_status: str = Field(..., description="Approval status: 'approved', 'rejected', or 'pending'")
    expert_notes: Optional[str] = Field(None, description="Clinical reviewer observations or reason")


class EvaluationReviewResponse(BaseModel):
    status: str
    message: str
    item_id: str
    new_status: str

