"""
Embedding outlier detection package.

Provides real TF-IDF centroid distance outlier detection
and 2D PCA projection coordinates.
"""

from scoring.embeddings.outlier_detector import (
    compute_tfidf_outlier_scores,
    extract_item_text,
)

__all__ = [
    "compute_tfidf_outlier_scores",
    "extract_item_text",
]
