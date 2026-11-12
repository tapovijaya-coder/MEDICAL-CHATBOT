"""MediBot AI Backend Package Initialization."""
import os
import sys

# Prevent Windows Intel OpenMP / Microsoft OpenMP collision between PyTorch and FAISS
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Ensure root directory is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

