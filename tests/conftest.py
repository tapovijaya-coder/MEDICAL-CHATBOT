"""Pytest global configuration."""
import os
import sys

# Windows OpenMP compatibility between PyTorch and FAISS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Pre-import faiss before any tests run
import faiss

# Ensure root path in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


