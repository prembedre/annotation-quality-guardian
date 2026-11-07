"""
Inter-annotator agreement metrics.

Implements Cohen's Kappa (2 annotators) and Fleiss' Kappa (3+ annotators).
"""

from typing import Dict, List
import numpy as np


def cohens_kappa(labels_a: List[str], labels_b: List[str]) -> float:
    """
    Compute Cohen's Kappa for two annotators.

    Args:
        labels_a: Labels assigned by annotator A.
        labels_b: Labels assigned by annotator B (same items, same order).

    Returns:
        Cohen's Kappa coefficient (float in [-1, 1]).

    Raises:
        ValueError: If input lists have different lengths or are empty.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("Label lists must have the same length.")
    if len(labels_a) == 0:
        raise ValueError("Label lists must not be empty.")

    n = len(labels_a)
    categories = sorted(set(labels_a) | set(labels_b))
    cat_index = {c: i for i, c in enumerate(categories)}
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
    Compute Fleiss' Kappa for 3+ annotators.

    Args:
        ratings_matrix: A list of items, where each item is a list of
                        counts per category. E.g., [[3, 0, 1], [2, 2, 0]]
                        means 4 annotators rated 2 items across 3 categories.

    Returns:
        Fleiss' Kappa coefficient (float).

    Raises:
        ValueError: If the matrix is empty or inconsistent.
    """
    mat = np.array(ratings_matrix, dtype=float)
    if mat.size == 0:
        raise ValueError("Ratings matrix must not be empty.")

    N = mat.shape[0]       # number of items
    n = mat.sum(axis=1)[0] # number of raters per item
    k = mat.shape[1]       # number of categories

    # Proportion of assignments to each category
    p_j = mat.sum(axis=0) / (N * n)

    # Per-item agreement
    P_i = (np.sum(mat ** 2, axis=1) - n) / (n * (n - 1))

    P_bar = np.mean(P_i)
    P_e = np.sum(p_j ** 2)

    if P_e == 1.0:
        return 1.0

    return float((P_bar - P_e) / (1 - P_e))
