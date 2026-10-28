
"""
Inter-annotator agreement metrics.

Implements Cohen's Kappa (2 annotators) and Fleiss' Kappa
for multiple annotators.
"""

from typing import List
import numpy as np


def cohens_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    """
    Compute Cohen's Kappa for two annotators.

    Args:
        labels_a: Labels assigned by annotator A.
        labels_b: Labels assigned by annotator B for the same items,
                  in the same order.

    Returns:
        Cohen's Kappa coefficient.

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("Label lists must have the same length.")

    if len(labels_a) == 0:
        raise ValueError("Label lists must not be empty.")

    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    cat_index = {category: index for index, category in enumerate(categories)}
    k = len(categories)

    # Build confusion matrix
    matrix = np.zeros((k, k), dtype=int)

    for a, b in zip(labels_a, labels_b):
        matrix[cat_index[a]][cat_index[b]] += 1

    # Observed agreement
    p_o = np.trace(matrix) / n

    # Expected agreement
    row_sums = matrix.sum(axis=1)
    col_sums = matrix.sum(axis=0)
    p_e = np.sum(row_sums * col_sums) / (n * n)

    if p_e == 1.0:
        return 1.0

    return float((p_o - p_e) / (1 - p_e))


def fleiss_kappa(ratings_matrix: List[List[int]]) -> float:
    """
    Compute Fleiss' Kappa for multiple annotators.

    Each row represents an item, and each column represents the
    number of ratings assigned to a category.

    Example:
        [[3, 0], [0, 3]]
        Two items, two categories, and three ratings per item.

    Returns:
        Fleiss' Kappa coefficient.

    Raises:
        ValueError: If the matrix is empty or invalid.
    """
    mat = np.array(ratings_matrix, dtype=float)

    # Validate matrix
    if mat.size == 0:
        raise ValueError("Ratings matrix must not be empty.")

    if mat.ndim != 2:
        raise ValueError("Ratings matrix must be two-dimensional.")

    if mat.shape[0] < 1 or mat.shape[1] < 2:
        raise ValueError(
            "Ratings matrix must contain items and at least two categories."
        )

    if not np.all(np.isfinite(mat)):
        raise ValueError("Rating counts must be finite numbers.")

    if np.any(mat < 0):
        raise ValueError("Rating counts cannot be negative.")

    if not np.all(mat == np.floor(mat)):
        raise ValueError("Rating counts must be integers.")

    # Each item must have the same number of ratings
    row_sums = mat.sum(axis=1)

    if not np.all(row_sums == row_sums[0]):
        raise ValueError(
            "Each item must have the same number of ratings."
        )

    # At least two ratings per item are required
    n = row_sums[0]

    if n < 2:
        raise ValueError(
            "Each item must have at least two ratings."
        )

    N = mat.shape[0]

    # Proportion of assignments to each category
    p_j = mat.sum(axis=0) / (N * n)

    # Per-item agreement
    P_i = (np.sum(mat ** 2, axis=1) - n) / (n * (n - 1))

    # Mean observed agreement
    P_bar = np.mean(P_i)

    # Expected agreement by chance
    P_e = np.sum(p_j ** 2)

    if P_e == 1.0:
        return 1.0

    return float((P_bar - P_e) / (1 - P_e))
