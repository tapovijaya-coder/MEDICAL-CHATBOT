"""Embeddings generation module using Hugging Face Sentence Transformers."""
import os
import logging
from typing import List, Optional
import numpy as np

# Ensure Windows OpenMP compatibility
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

logger = logging.getLogger("medibot.embeddings")

DEFAULT_MODEL_NAME = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


class EmbeddingManager:
    """Manages Hugging Face Sentence Transformers for generating vector embeddings."""
    _instance: Optional["EmbeddingManager"] = None
    _model = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(EmbeddingManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        if self._model is None:
            self.model_name = model_name
            self._load_model()

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {self.model_name}...")
            # First attempt loading from local cache to avoid network timeout
            try:
                self._model = SentenceTransformer(self.model_name, local_files_only=True)
                logger.info("Loaded embedding model from local cache.")
            except Exception:
                self._model = SentenceTransformer(self.model_name)
                logger.info("Embedding model loaded from hub.")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer '{self.model_name}': {e}")
            raise e

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embedding vectors for a list of document strings."""
        if not texts:
            return []
        if self._model is None:
            self._load_model()
        
        # Normalize embeddings for cosine similarity
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generates embedding vector for a single query string."""
        if self._model is None:
            self._load_model()
        
        embedding = self._model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()

    @property
    def dimension(self) -> int:
        """Returns the vector dimensionality (384 for all-MiniLM-L6-v2)."""
        if self._model is not None:
            if hasattr(self._model, "get_embedding_dimension"):
                return self._model.get_embedding_dimension()
            return self._model.get_sentence_embedding_dimension()
        return 384


def get_embedding_manager(model_name: str = DEFAULT_MODEL_NAME) -> EmbeddingManager:
    """Factory function to retrieve the singleton EmbeddingManager."""
    return EmbeddingManager(model_name=model_name)
