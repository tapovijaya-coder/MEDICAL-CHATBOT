"""Script to index Gale Encyclopedia (759 pages) and modern authoritative clinical guidelines."""
import os
import sys
import time
import json
import logging

# Ensure project root in sys.path and set OpenMP fix
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.medical_extractor import extract_and_chunk_encyclopedia
from backend.vectorstore import get_vector_store
from backend.authoritative_ingestion import get_authoritative_manager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("index_kb")


def run_indexing():
    pdf_path = os.path.join("data", "uploaded_pdfs", "The_GALE_ENCYCLOPEDIA_of_MEDICINE_SECOND.pdf")
    if not os.path.exists(pdf_path):
        logger.error(f"Gale Encyclopedia not found at {pdf_path}")
        return

    logger.info(f"Extracting and categorizing Gale Encyclopedia from {pdf_path}...")
    t0 = time.time()
    chunks, doc_info, report = extract_and_chunk_encyclopedia(
        pdf_path=pdf_path,
        chunk_size=1200,
        chunk_overlap=250
    )
    t1 = time.time()
    logger.info(f"Extracted {len(chunks)} chunks across {report['successful_pages']} pages in {t1-t0:.2f}s.")

    # Save extraction report to disk
    report_path = os.path.join("vectorstore", "gale_extraction_report.json")
    os.makedirs("vectorstore", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    logger.info(f"Extraction report saved to {report_path}")

    # Add Gale Encyclopedia to vector store
    vs = get_vector_store()
    logger.info(f"Indexing {len(chunks)} chunks into FAISS vector store and BM25 index...")
    t2 = time.time()
    vs.add_document(chunks, doc_info)
    t3 = time.time()
    logger.info(f"Gale Encyclopedia indexed in {t3-t2:.2f}s! Vector store now has {vs.total_chunks} chunks.")

    # Index modern authoritative guidelines (WHO, ICMR, CDC, MedlinePlus)
    logger.info("Indexing modern authoritative guidelines (WHO 2023, ICMR 2023, CDC 2024, NIH 2024)...")
    auth_mgr = get_authoritative_manager()
    for g in auth_mgr.get_curated_guidelines():
        g_id = f"auth_{g['publication_year']}_{g['medical_category'].replace(' ', '_')}"
        g_chunks = [{
            "text": g["content"],
            "metadata": {
                "document_id": g_id,
                "document_name": g["document_name"],
                "source": g["source"],
                "edition": g["edition"],
                "publication_year": g["publication_year"],
                "page_number": 1,
                "page": 1,
                "medical_category": g["medical_category"],
                "section_title": g["title"],
                "source_type": g["source_type"],
                "is_historical": g["is_historical"],
                "chunk_id": f"{g_id}_p1_c1"
            }
        }]
        g_doc = {
            "document_id": g_id,
            "filename": g["document_name"],
            "pages": 1,
            "chunks": 1,
            "file_size_bytes": len(g["content"]),
            "edition": g["edition"],
            "publication_year": g["publication_year"],
            "source_type": g["source_type"],
            "is_historical": g["is_historical"],
            "medical_categories": [g["medical_category"]]
        }
        vs.add_document(g_chunks, g_doc)

    logger.info(f"Complete Knowledge Base Indexing Finished! Total documents: {vs.total_documents}, Total vectors: {vs.total_chunks}")


if __name__ == "__main__":
    run_indexing()

