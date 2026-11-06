"""
Text Embedding Outlier Detection and Dimensionality Reduction.

Uses TF-IDF vectorization with cosine distance to class/dataset centroids,
and real 2D PCA projection for latent space visualization.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import PCA


def extract_item_text(content: Any) -> str:
    """Extract plain text string from item content dictionary or primitive."""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, dict):
        for key in ["text", "sentence", "input", "body", "content", "document", "prompt"]:
            val = content.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        # Fallback to combining non-empty string values
        parts = [str(v) for v in content.values() if v and not isinstance(v, (dict, list))]
        if parts:
            return " ".join(parts)
        return str(content)
    return str(content) if content else ""


def compute_tfidf_outlier_scores(
    items_data: List[Dict[str, Any]],
    outlier_threshold: float = 0.70,
) -> List[Dict[str, Any]]:
    """
    Compute real TF-IDF embedding outlier scores and 2D PCA coordinates.

    Args:
        items_data: List of dicts, each with keys:
            - 'item_id': int
            - 'content': dict or str
            - 'label': optional str class label
        outlier_threshold: Distance threshold above which item is marked as outlier

    Returns:
        List of dicts with 'item_id', 'outlier_score', 'is_outlier',
        'embedding' (2D PCA coordinates), 'nearest_item_id', and 'details'.
    """
    if not items_data:
        return []

    n_items = len(items_data)
    texts = [extract_item_text(it.get("content")) for it in items_data]
    item_ids = [it.get("item_id") for it in items_data]
    labels = [it.get("label") for it in items_data]

    # Ensure texts are not all blank
    if all(not t for t in texts):
        texts = [f"item_{it_id}" for it_id in item_ids]

    # Vectorize texts with TF-IDF
    try:
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            min_df=1,
            token_pattern=r"(?u)\b\w+\b",
        )
        X = vectorizer.fit_transform(texts).toarray()
    except Exception:
        # Fallback if vocabulary is completely empty
        X = np.eye(n_items)

    # Compute 2D projection via PCA
    if n_items >= 2:
        try:
            n_components = min(2, X.shape[1], n_items)
            pca = PCA(n_components=n_components, random_state=42)
            coords_raw = pca.fit_transform(X)
            if n_components == 1:
                coords_2d = [[float(c[0]), 0.0] for c in coords_raw]
            else:
                coords_2d = [[float(c[0]), float(c[1])] for c in coords_raw]
        except Exception:
            coords_2d = [[0.0, 0.0] for _ in range(n_items)]
    else:
        coords_2d = [[0.0, 0.0] for _ in range(n_items)]

    # Compute Class Centroids or Global Centroid
    # Group items by label where available
    class_indices: Dict[str, List[int]] = {}
    for idx, lbl in enumerate(labels):
        if lbl:
            class_indices.setdefault(lbl, []).append(idx)

    # Global centroid
    global_centroid = np.mean(X, axis=0)
    norm_gc = np.linalg.norm(global_centroid)
    if norm_gc > 1e-9:
        global_centroid = global_centroid / norm_gc

    # Class-specific normalized centroids
    class_centroids: Dict[str, np.ndarray] = {}
    for lbl, indices in class_indices.items():
        if len(indices) >= 2:
            c = np.mean(X[indices], axis=0)
            norm_c = np.linalg.norm(c)
            if norm_c > 1e-9:
                class_centroids[lbl] = c / norm_c

    # Pairwise cosine similarity matrix between items for nearest neighbor
    norms = np.linalg.norm(X, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    X_norm = X / norms
    sim_matrix = np.dot(X_norm, X_norm.T)

    results = []
    for idx in range(n_items):
        item_vec = X_norm[idx]
        lbl = labels[idx]

        # Leave-one-out centroid so the item does not dilute its own comparison baseline
        class_others = [j for j in class_indices.get(lbl, []) if j != idx]
        if len(class_others) >= 1:
            c = np.mean(X[class_others], axis=0)
            norm_c = np.linalg.norm(c)
            centroid = c / norm_c if norm_c > 1e-9 else global_centroid
        else:
            global_others = [j for j in range(n_items) if j != idx]
            if len(global_others) >= 1:
                c = np.mean(X[global_others], axis=0)
                norm_c = np.linalg.norm(c)
                centroid = c / norm_c if norm_c > 1e-9 else global_centroid
            else:
                centroid = global_centroid

        cos_sim = float(np.dot(item_vec, centroid))
        # Cosine distance: 1 - cos_sim bounded in [0.0, 1.0]
        cos_dist = max(0.0, min(1.0, 1.0 - cos_sim))

        outlier_score = round(cos_dist, 4)
        is_outlier = outlier_score >= outlier_threshold

        # Find nearest neighbor (other item with highest similarity)
        nearest_id = None
        if n_items > 1:
            sims = sim_matrix[idx].copy()
            sims[idx] = -1.0  # exclude self
            nearest_idx = int(np.argmax(sims))
            nearest_id = item_ids[nearest_idx]

        results.append({
            "item_id": item_ids[idx],
            "outlier_score": outlier_score,
            "is_outlier": is_outlier,
            "embedding": [round(coords_2d[idx][0], 4), round(coords_2d[idx][1], 4)],
            "nearest_item_id": nearest_id,
            "details": {
                "cosine_distance": outlier_score,
                "projection_2d": [round(coords_2d[idx][0], 4), round(coords_2d[idx][1], 4)],
                "method": "tfidf_centroid_distance",
                "nearest_item_id": nearest_id,
                "label": lbl,
            },
        })

    return results
