"""Advanced Medical Document & Knowledge Extraction Engine for MediBot AI.
Processes medical reference books, encyclopedias, and clinical guidelines.
"""
import re
import os
import uuid
import logging
from typing import List, Dict, Any, Tuple, Optional
import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger("medibot.extractor")

# The 16 Official Medical Taxonomy Categories
MEDICAL_CATEGORIES = [
    "General Medicine",
    "Cardiology",
    "Neurology",
    "Psychiatry and Mental Health",
    "Dermatology",
    "Gastroenterology",
    "Endocrinology",
    "Respiratory Diseases",
    "Infectious Diseases",
    "Orthopedics",
    "Pediatrics",
    "Women's Health",
    "Diagnostic Procedures",
    "Medical Terminology",
    "Preventive Healthcare",
    "Emergency Medicine"
]

# Keywords taxonomy for semantic classification
CATEGORY_TAXONOMY = {
    "Cardiology": [
        "heart", "cardiac", "cardio", "coronary", "artery", "arterial", "hypertension",
        "hypotension", "myocardial", "infarction", "angina", "arrhythmia", "vascular",
        "ventricular", "atrial", "aorta", "pericard", "endocard", "cholesterol", "blood pressure"
    ],
    "Neurology": [
        "brain", "neurol", "nervous", "seizure", "epilepsy", "stroke", "cerebral",
        "paralysis", "nerve", "cranial", "spinal", "meningitis", "encephalitis",
        "dementia", "alzheimer", "parkinson", "neuropathy", "headache", "migraine", "synapse"
    ],
    "Psychiatry and Mental Health": [
        "depress", "anxiety", "schizo", "psychiat", "psycholog", "bipolar", "phobia",
        "panic", "disorder", "behavior", "mental", "cognitive", "delusion", "hallucination",
        "ptsd", "trauma", "addiction", "substance", "psychosis", "suicid"
    ],
    "Dermatology": [
        "skin", "dermat", "lesion", "rash", "eczema", "psoriasis", "melanoma", "carcinoma",
        "epiderm", "cutaneous", "hair", "nail", "acne", "ulcer", "blister", "pruritus"
    ],
    "Gastroenterology": [
        "stomach", "gastric", "gastro", "intestin", "colon", "bowel", "liver", "hepatic",
        "pancreas", "hepatitis", "cirrhosis", "ulcer", "diarrhea", "esophag", "reflux",
        "crohn", "colitis", "gallbladder", "biliary", "digestive", "abdomen"
    ],
    "Endocrinology": [
        "diabetes", "insulin", "glucose", "thyroid", "hormone", "endocrine", "adrenal",
        "pituitary", "metabolic", "hyperthyroid", "hypothyroid", "cushing", "addison",
        "glycemic", "pancreatic", "ketoacidosis"
    ],
    "Respiratory Diseases": [
        "lung", "pulmonary", "respiratory", "bronch", "asthma", "copd", "pneumonia",
        "emphysema", "pleural", "breath", "oxygen", "alveoli", "trachea", "hypoxia"
    ],
    "Infectious Diseases": [
        "infect", "bacteri", "viral", "virus", "fungal", "parasite", "antibiotic",
        "fever", "tuberculosis", "hiv", "aids", "influenza", "malaria", "sepsis", "pathogen"
    ],
    "Orthopedics": [
        "bone", "fracture", "joint", "orthoped", "musculoskeletal", "muscle", "tendon",
        "ligament", "cartilage", "arthritis", "osteoporosis", "spine", "vertebra", "dislocation"
    ],
    "Pediatrics": [
        "child", "infant", "pediatr", "neonatal", "congenital", "newborn", "developmental",
        "growth", "vaccination", "pediatric", "toddler", "adolescent"
    ],
    "Women's Health": [
        "cervical", "uterine", "ovarian", "breast", "pregnancy", "prenatal", "obstetric",
        "gynecol", "menopause", "menstrual", "vagina", "placenta", "fertility"
    ],
    "Diagnostic Procedures": [
        "biopsy", "mri", "ct scan", "computed tomography", "ultrasound", "endoscopy",
        "radiography", "x-ray", "blood test", "diagnostic", "examination", "screening",
        "electrocardiogram", "ecg", "eeg", "laboratory", "urinalysis"
    ],
    "Medical Terminology": [
        "key terms", "definition", "terminology", "glossary", "etymology", "vocabulary",
        "medical terms", "suffix", "prefix"
    ],
    "Preventive Healthcare": [
        "prevention", "lifestyle", "diet", "exercise", "nutrition", "screening", "prophylaxis",
        "immunization", "wellness", "risk reduction", "hygiene", "smoking cessation"
    ],
    "Emergency Medicine": [
        "emergency", "cardiac arrest", "cpr", "resuscitation", "shock", "trauma",
        "acute", "overdose", "poison", "life-threatening", "unresponsive", "hemorrhage"
    ]
}

# Standard section header regex patterns found in Gale Encyclopedia & Medical Literature
SECTION_PATTERNS = [
    (r"\bDEFINITION\b", "Definition"),
    (r"\bDESCRIPTION\b", "Description"),
    (r"\bCAUSES\s+AND\s+SYMPTOMS\b", "Causes and Symptoms"),
    (r"\bCAUSES\b", "Causes"),
    (r"\bSYMPTOMS\b", "Symptoms"),
    (r"\bDIAGNOSIS\b", "Diagnosis"),
    (r"\bTREATMENT\b", "Treatment"),
    (r"\bALTERNATIVE\s+TREATMENT\b", "Alternative Treatment"),
    (r"\bPROGNOSIS\b", "Prognosis"),
    (r"\bPREVENTION\b", "Prevention"),
    (r"\bKEY\s+TERMS\b", "Key Terms"),
    (r"\bRESOURCES\b", "Resources"),
    (r"\bORGANIZATIONS\b", "Organizations")
]


def classify_text_category(text: str, default: str = "General Medicine") -> str:
    """Classifies a medical passage into one of the 16 medical categories."""
    lower = text.lower()
    scores: Dict[str, int] = {cat: 0 for cat in MEDICAL_CATEGORIES}

    for cat, keywords in CATEGORY_TAXONOMY.items():
        for kw in keywords:
            if kw in lower:
                scores[cat] += 1

    # Select category with highest score
    best_cat, best_score = max(scores.items(), key=lambda item: item[1])
    return best_cat if best_score > 0 else default


def detect_document_metadata(filename: str, sample_text: str) -> Dict[str, Any]:
    """Infers edition, publication year, and historical reference status."""
    meta = {
        "document_name": filename,
        "edition": "Standard Edition",
        "publication_year": 2024,
        "source_type": "clinical_reference",
        "is_historical": False
    }

    lower_name = filename.lower()
    lower_text = sample_text.lower()

    if "gale" in lower_name or "encyclopedia" in lower_name:
        meta["document_name"] = filename
        meta["edition"] = "Second Edition"
        meta["publication_year"] = 2002
        meta["source_type"] = "medical_reference_book"
        meta["is_historical"] = True
    elif "200" in lower_text or "199" in lower_text:
        match = re.search(r"\b(19\d{2}|20[0-2]\d)\b", sample_text)
        if match:
            year = int(match.group(1))
            meta["publication_year"] = year
            meta["is_historical"] = (year < 2015)

    return meta


def extract_and_chunk_encyclopedia(
    pdf_path: str,
    document_id: Optional[str] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    High-performance PyMuPDF extraction & semantic chunking pipeline.
    Preserves exact 1-indexed page numbers, identifies headings, categorizes into 16 domains,
    and formats metadata according to Phase 3 requirements.
    """
    if document_id is None:
        document_id = str(uuid.uuid4())

    filename = os.path.basename(pdf_path)
    logger.info(f"Initiating extraction on '{filename}' using PyMuPDF...")

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    
    # Read sample text for document metadata
    sample_text = ""
    for p in range(min(5, total_pages)):
        sample_text += doc[p].get_text() + "\n"
        
    doc_meta = detect_document_metadata(filename, sample_text)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len
    )

    all_chunks: List[Dict[str, Any]] = []
    successful_pages = 0
    failed_pages = 0
    total_chars = 0
    category_counts: Dict[str, int] = {cat: 0 for cat in MEDICAL_CATEGORIES}
    sections_found: set = set()
    current_topic = filename.replace(".pdf", "").replace("_", " ")

    for page_idx in range(total_pages):
        page_num = page_idx + 1
        try:
            page = doc[page_idx]
            raw_text = page.get_text()
            
            if not raw_text or not raw_text.strip():
                # Try OCR or layout text if empty
                raw_text = page.get_text("blocks")
                if isinstance(raw_text, list):
                    raw_text = "\n".join([b[4] for b in raw_text if len(b) > 4])
                else:
                    raw_text = ""

            if not raw_text.strip():
                failed_pages += 1
                continue

            cleaned = raw_text.replace("\x00", "").strip()
            total_chars += len(cleaned)
            successful_pages += 1

            # Check for topic header or section headers on this page
            first_lines = [l.strip() for l in cleaned.split("\n")[:4] if l.strip()]
            for l in first_lines:
                if len(l) > 3 and len(l) < 60 and not any(h in l.upper() for h in ["GALE", "ENCYCLOPEDIA", "PAGE", "INDEX"]):
                    if l.isupper() or l.istitle():
                        current_topic = l
                        break

            # Identify section title on page
            detected_section = "General Clinical Reference"
            for pattern, sec_name in SECTION_PATTERNS:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    detected_section = f"{current_topic} - {sec_name}"
                    sections_found.add(sec_name)
                    break

            # Medical Category Classification
            med_category = classify_text_category(cleaned)
            category_counts[med_category] += 1

            # Split into semantic chunks
            page_splits = text_splitter.split_text(cleaned)

            for c_idx, split_text in enumerate(page_splits, 1):
                chunk_id = f"{document_id}_p{page_num}_c{c_idx}"
                
                # Strict Schema Compliance with Phase 3
                chunk_metadata = {
                    "document_id": document_id,
                    "document_name": filename,
                    "source": filename,
                    "edition": doc_meta["edition"],
                    "publication_year": doc_meta["publication_year"],
                    "page_number": page_num,
                    "page": page_num,
                    "medical_category": med_category,
                    "section_title": detected_section,
                    "source_type": doc_meta["source_type"],
                    "chunk_id": chunk_id,
                    "is_historical": doc_meta["is_historical"],
                    "content": split_text
                }

                all_chunks.append({
                    "text": split_text,
                    "metadata": chunk_metadata
                })

        except Exception as e:
            logger.warning(f"Failed to process page {page_num}: {e}")
            failed_pages += 1

    doc.close()

    extraction_report = {
        "document_name": filename,
        "total_pages": total_pages,
        "successful_pages": successful_pages,
        "failed_pages": failed_pages,
        "extracted_text_size_bytes": total_chars,
        "number_of_medical_sections": len(sections_found),
        "sections_detected": list(sections_found),
        "number_of_generated_chunks": len(all_chunks),
        "category_distribution": {k: v for k, v in category_counts.items() if v > 0},
        "publication_year": doc_meta["publication_year"],
        "is_historical": doc_meta["is_historical"]
    }

    doc_info = {
        "document_id": document_id,
        "filename": filename,
        "pages": total_pages,
        "chunks": len(all_chunks),
        "file_size_bytes": os.path.getsize(pdf_path) if os.path.exists(pdf_path) else total_chars,
        "edition": doc_meta["edition"],
        "publication_year": doc_meta["publication_year"],
        "source_type": doc_meta["source_type"],
        "is_historical": doc_meta["is_historical"],
        "medical_categories": [k for k, v in category_counts.items() if v > 0]
    }

    logger.info(
        f"Extraction complete for '{filename}': {successful_pages}/{total_pages} pages processed -> "
        f"{len(all_chunks)} chunks created."
    )
    return all_chunks, doc_info, extraction_report
