"""FAISS Vector Store and Hybrid Retrieval Engine for MediBot AI."""
import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple, Set
import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from backend.embeddings import get_embedding_manager

logger = logging.getLogger("medibot.vectorstore")

DEFAULT_VECTORSTORE_DIR = os.getenv("VECTORSTORE_DIR", "vectorstore")

# Clinical acronym expansions to improve retrieval recall
CLINICAL_ACRONYMS = {
    r"\bhtn\b": "hypertension high blood pressure",
    r"\bt2dm\b": "type 2 diabetes mellitus",
    r"\bdm2\b": "type 2 diabetes mellitus",
    r"\bdm\b": "diabetes mellitus",
    r"\bmi\b": "myocardial infarction heart attack",
    r"\bcopd\b": "chronic obstructive pulmonary disease",
    r"\bchf\b": "congestive heart failure",
    r"\bcad\b": "coronary artery disease",
    r"\bcva\b": "cerebrovascular accident stroke",
    r"\bgerd\b": "gastroesophageal reflux disease",
    r"\bpud\b": "peptic ulcer disease",
    r"\bcpr\b": "cardiopulmonary resuscitation",
    r"\baed\b": "automated external defibrillator",
    r"\bpca\b": "patient controlled analgesia",
    r"\bsob\b": "shortness of breath dyspnea"
}


def rewrite_medical_query(query: str) -> str:
    """Expands clinical acronyms and standardizes query terminology."""
    expanded = query
    lower = query.lower()
    for pattern, expansion in CLINICAL_ACRONYMS.items():
        if re.search(pattern, lower):
            expanded += f" ({expansion})"
    return expanded


class FAISSStore:
    """Manages FAISS dense vector search, BM25 sparse keyword search, and metadata registry."""
    _instance: Optional["FAISSStore"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FAISSStore, cls).__new__(cls)
        return cls._instance

    def __init__(self, storage_dir: str = DEFAULT_VECTORSTORE_DIR):
        self.storage_dir = storage_dir
        self.index_path = os.path.join(self.storage_dir, "faiss.index")
        self.chunks_path = os.path.join(self.storage_dir, "chunks.json")
        self.registry_path = os.path.join(self.storage_dir, "registry.json")
        
        self.embedding_manager = get_embedding_manager()
        self.dimension = self.embedding_manager.dimension
        
        os.makedirs(self.storage_dir, exist_ok=True)
        
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Dict[str, Any]] = []
        self.registry: Dict[str, Dict[str, Any]] = {}
        self.bm25: Optional[BM25Okapi] = None
        self._bm25_corpus: List[List[str]] = []
        
        self._load_store()

    def _load_store(self):
        """Loads index, chunks, and document registry from disk if available."""
        # 1. Load registry
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
                logger.info(f"Loaded {len(self.registry)} document(s) from registry.")
            except Exception as e:
                logger.warning(f"Could not load registry: {e}. Resetting registry.")
                self.registry = {}
        else:
            self.registry = {}

        # 2. Load chunks
        if os.path.exists(self.chunks_path):
            try:
                with open(self.chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded {len(self.chunks)} chunk(s) from disk.")
            except Exception as e:
                logger.warning(f"Could not load chunks: {e}. Resetting chunks.")
                self.chunks = []
        else:
            self.chunks = []

        # 3. Load FAISS index
        if os.path.exists(self.index_path) and len(self.chunks) > 0:
            try:
                self.index = faiss.read_index(self.index_path)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors.")
            except Exception as e:
                logger.warning(f"Could not load FAISS index: {e}. Rebuilding from chunks.")
                self._rebuild_index()
        else:
            self.index = faiss.IndexFlatIP(self.dimension)
            logger.info("Created new empty FAISS IndexFlatIP.")

        # 4. Initialize BM25 sparse keyword retriever
        self._init_bm25()

    def _init_bm25(self):
        """Initializes or refreshes the BM25 index from chunk text tokens."""
        if not self.chunks:
            self.bm25 = None
            self._bm25_corpus = []
            return
        
        tokenized_corpus = [
            re.findall(r"\w+", chunk.get("text", "").lower())
            for chunk in self.chunks
        ]
        self._bm25_corpus = tokenized_corpus
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 keyword index initialized for {len(tokenized_corpus)} chunks.")

    def _save_store(self):
        """Persists FAISS index, chunks, and registry to disk."""
        try:
            if self.index is not None:
                faiss.write_index(self.index, self.index_path)
            
            with open(self.chunks_path, "w", encoding="utf-8") as f:
                json.dump(self.chunks, f, ensure_ascii=False, indent=2)
                
            with open(self.registry_path, "w", encoding="utf-8") as f:
                json.dump(self.registry, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Vector store successfully persisted. (Vectors: {len(self.chunks)})")
        except Exception as e:
            logger.error(f"Error persisting vector store: {e}")
            raise e

    def _rebuild_index(self):
        """Rebuilds the FAISS index and BM25 model from the current in-memory chunks list."""
        self.index = faiss.IndexFlatIP(self.dimension)
        if not self.chunks:
            self._save_store()
            self._init_bm25()
            return
        
        texts = [chunk["text"] for chunk in self.chunks]
        # Batch embedding generation
        batch_size = 128
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            emb = self.embedding_manager.embed_documents(batch_texts)
            all_embeddings.extend(emb)

        vectors = np.array(all_embeddings, dtype=np.float32)
        self.index.add(vectors)
        self._save_store()
        self._init_bm25()
        logger.info(f"Rebuilt FAISS index with {self.index.ntotal} vectors.")

    def add_document(self, chunks: List[Dict[str, Any]], doc_info: Dict[str, Any]):
        """
        Incrementally embeds chunks, adds them to FAISS & BM25, and records the document in registry.
        Preserves existing documents and performs duplicate detection.
        """
        if not chunks:
            doc_info["upload_date"] = datetime.now(timezone.utc).isoformat()
            self.registry[doc_info["document_id"]] = doc_info
            self._save_store()
            return

        # Deduplicate chunks against existing chunk_ids
        existing_chunk_ids = {c["metadata"].get("chunk_id") for c in self.chunks if "chunk_id" in c.get("metadata", {})}
        unique_chunks = [c for c in chunks if c["metadata"].get("chunk_id") not in existing_chunk_ids]

        if unique_chunks:
            texts = [c["text"] for c in unique_chunks]
            batch_size = 128
            all_embeddings = []
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                emb = self.embedding_manager.embed_documents(batch_texts)
                all_embeddings.extend(emb)

            vectors = np.array(all_embeddings, dtype=np.float32)

            if self.index is None:
                self.index = faiss.IndexFlatIP(self.dimension)
                
            self.index.add(vectors)
            self.chunks.extend(unique_chunks)
            logger.info(f"Added {len(unique_chunks)} new chunks to FAISS index. Total: {len(self.chunks)}.")
        else:
            logger.info("All chunks already indexed (duplicate detection).")

        doc_info["upload_date"] = datetime.now(timezone.utc).isoformat()
        self.registry[doc_info["document_id"]] = doc_info
        
        self._save_store()
        self._init_bm25()

    def delete_document(self, document_id: str) -> bool:
        """Deletes all chunks belonging to document_id, removes from registry, and updates FAISS & BM25."""
        if document_id not in self.registry:
            logger.warning(f"Document ID {document_id} not found in registry.")
            return False

        del self.registry[document_id]
        
        # Keep only chunks not belonging to the deleted document
        self.chunks = [c for c in self.chunks if c["metadata"].get("document_id") != document_id]
        
        # Rebuild FAISS index with remaining chunks
        self._rebuild_index()
        logger.info(f"Successfully deleted document {document_id} and updated vector index.")
        return True

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced Hybrid Retrieval combining:
        1. Dense semantic search (FAISS)
        2. Sparse keyword search (BM25)
        3. Reciprocal Rank Fusion (RRF)
        4. Optional medical category filtering
        """
        if self.index is None or self.index.ntotal == 0 or len(self.chunks) == 0:
            return []

        expanded_query = rewrite_medical_query(query)
        candidates_k = min(top_k * 4, len(self.chunks))

        # --- 1. Dense Semantic Search (FAISS) ---
        query_vector = np.array([self.embedding_manager.embed_query(expanded_query)], dtype=np.float32)
        dense_scores, dense_indices = self.index.search(query_vector, candidates_k)

        dense_ranks: Dict[int, int] = {}
        for rank, idx in enumerate(dense_indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                dense_ranks[idx] = rank + 1

        # --- 2. Sparse Keyword Search (BM25) ---
        bm25_ranks: Dict[int, int] = {}
        if self.bm25 is not None:
            tokenized_query = re.findall(r"\w+", expanded_query.lower())
            bm25_scores = self.bm25.get_scores(tokenized_query)
            top_bm25_indices = np.argsort(bm25_scores)[::-1][:candidates_k]
            for rank, idx in enumerate(top_bm25_indices):
                if bm25_scores[idx] > 0.0:
                    bm25_ranks[idx] = rank + 1

        # --- 3. Reciprocal Rank Fusion (RRF) ---
        all_candidate_indices = set(dense_ranks.keys()).union(set(bm25_ranks.keys()))
        rrf_scores: Dict[int, float] = {}

        rrf_constant = 60.0
        for idx in all_candidate_indices:
            score = 0.0
            if idx in dense_ranks:
                score += 1.0 / (rrf_constant + dense_ranks[idx])
            if idx in bm25_ranks:
                score += 1.0 / (rrf_constant + bm25_ranks[idx])

            # Category filter bonus or strict filtering
            chunk_meta = self.chunks[idx].get("metadata", {})
            chunk_cat = chunk_meta.get("medical_category", "")
            
            if category_filter and category_filter != "All":
                if chunk_cat.lower() == category_filter.lower():
                    score *= 1.5
                else:
                    score *= 0.3

            rrf_scores[idx] = score

        # Sort by RRF score descending
        sorted_indices = sorted(rrf_scores.keys(), key=lambda i: rrf_scores[i], reverse=True)[:top_k]

        results: List[Dict[str, Any]] = []
        for idx in sorted_indices:
            chunk = self.chunks[idx]
            meta = chunk.get("metadata", {})
            results.append({
                "text": chunk.get("text", ""),
                "source": meta.get("source") or meta.get("document_name") or "Medical Reference",
                "document_name": meta.get("document_name") or meta.get("source") or "Medical Reference",
                "page": meta.get("page") or meta.get("page_number") or 1,
                "page_number": meta.get("page_number") or meta.get("page") or 1,
                "edition": meta.get("edition", "Standard Edition"),
                "publication_year": meta.get("publication_year", 2024),
                "medical_category": meta.get("medical_category", "General Medicine"),
                "section_title": meta.get("section_title", "General"),
                "source_type": meta.get("source_type", "medical_reference"),
                "is_historical": meta.get("is_historical", False),
                "score": float(rrf_scores[idx])
            })

        return results

    def similarity_search(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Backwards-compatible interface delegating to hybrid_search."""
        return self.hybrid_search(query=query, top_k=top_k)

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return list(self.registry.values())

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        return self.registry.get(document_id)

    @property
    def total_documents(self) -> int:
        return len(self.registry)

    @property
    def total_chunks(self) -> int:
        return len(self.chunks)

    @property
    def total_pages(self) -> int:
        return sum(d.get("pages", 0) for d in self.registry.values())

    def get_categories_breakdown(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for c in self.chunks:
            cat = c.get("metadata", {}).get("medical_category", "General Medicine")
            counts[cat] = counts.get(cat, 0) + 1
        return counts


def get_vector_store(storage_dir: str = DEFAULT_VECTORSTORE_DIR) -> FAISSStore:
    return FAISSStore(storage_dir=storage_dir)
