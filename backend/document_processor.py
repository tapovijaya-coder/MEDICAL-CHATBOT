"""PDF Document processing and chunking module for MediBot AI."""
import io
import re
import uuid
import logging
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("medibot.document_processor")

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB max limit


def clean_text(text: str) -> str:
    """Cleans extracted raw text from PDF documents."""
    if not text:
        return ""
    # Remove null characters
    text = text.replace("\x00", "")
    # Normalize multiple whitespace and newlines while preserving paragraph structure
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def validate_pdf_content(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
    """Validates the uploaded file is a genuine, non-empty PDF within acceptable size limits."""
    if not filename.lower().endswith(".pdf"):
        return False, "Invalid file format. Only PDF (.pdf) documents are supported."
    
    if len(file_bytes) == 0:
        return False, "The uploaded file is empty (0 bytes)."
    
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"File size exceeds the maximum limit of {max_mb} MB."
    
    # Check PDF header magic bytes
    if not file_bytes.startswith(b"%PDF-"):
        return False, "The file does not appear to be a valid PDF document (missing %PDF- header)."
    
    return True, ""


def process_pdf(file_bytes: bytes, filename: str, document_id: str = None) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extracts text from each page using PyPDF and splits it into semantic chunks with metadata.
    
    Returns:
        chunks: List of dictionaries with 'text', 'metadata' (source, page, document_id, chunk_id)
        doc_info: Dictionary with 'pages', 'chunks', 'filename', 'document_id', 'file_size_bytes'
    """
    if document_id is None:
        document_id = str(uuid.uuid4())
    
    reader = PdfReader(io.BytesIO(file_bytes))
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The provided PDF has 0 readable pages.")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    
    all_chunks: List[Dict[str, Any]] = []
    chunk_counter = 0
    
    for page_idx, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        cleaned = clean_text(raw_text)
        
        if not cleaned:
            continue
        
        page_num = page_idx + 1
        page_splits = text_splitter.split_text(cleaned)
        
        for split_text in page_splits:
            if not split_text.strip():
                continue
            chunk_counter += 1
            all_chunks.append({
                "text": split_text,
                "metadata": {
                    "document_id": document_id,
                    "source": filename,
                    "page": page_num,
                    "chunk_id": f"{document_id}_{chunk_counter}",
                }
            })
    
    doc_info = {
        "document_id": document_id,
        "filename": filename,
        "pages": total_pages,
        "chunks": len(all_chunks),
        "file_size_bytes": len(file_bytes)
    }
    
    logger.info(f"Processed PDF '{filename}': {total_pages} pages -> {len(all_chunks)} chunks created.")
    return all_chunks, doc_info

