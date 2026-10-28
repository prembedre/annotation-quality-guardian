
import pytest

from scoring.gold_checker.checker import gold_accuracy
from scoring.agreement.kappa import cohens_kappa, fleiss_kappa


def test_gold_accuracy_correct_and_incorrect_labels():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
        {"item_id": "2", "annotator_id": "A", "label": "dog"},
        {"item_id": "3", "annotator_id": "B", "label": "bird"},
    ]
    gold_items = {"1": "cat", "2": "cat", "3": "bird"}

    result = gold_accuracy(annotations, gold_items)

    assert result["overall_accuracy"] == 0.6667
    assert result["per_annotator"]["A"]["accuracy"] == 0.5
    assert result["per_annotator"]["A"]["correct"] == 1
    assert result["per_annotator"]["A"]["total"] == 2


def test_gold_accuracy_ignores_items_without_gold_labels():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
        {"item_id": "unknown", "annotator_id": "A", "label": "dog"},
    ]

    result = gold_accuracy(annotations, {"1": "cat"})

    assert result["overall_accuracy"] == 1.0
    assert result["per_annotator"]["A"]["total"] == 1


def test_gold_accuracy_with_no_matching_items():
    annotations = [
        {"item_id": "unknown", "annotator_id": "A", "label": "cat"},
    ]

    result = gold_accuracy(annotations, {"1": "cat"})

    assert result["overall_accuracy"] == 0.0
    assert result["per_annotator"] == {}


def test_cohens_kappa_perfect_agreement():
    labels_a = ["cat", "dog", "bird", "cat"]
    labels_b = ["cat", "dog", "bird", "cat"]

    assert cohens_kappa(labels_a, labels_b) == pytest.approx(1.0)


def test_cohens_kappa_rejects_different_lengths():
    with pytest.raises(ValueError):
        cohens_kappa(["cat", "dog"], ["cat"])


def test_cohens_kappa_rejects_empty_lists():
    with pytest.raises(ValueError):
        cohens_kappa([], [])


def test_fleiss_kappa_perfect_agreement():
    ratings = [
        [3, 0],
        [0, 3],
        [3, 0],
    ]

    assert fleiss_kappa(ratings) == pytest.approx(1.0)


def test_fleiss_kappa_rejects_single_rating_per_item():
    ratings = [
        [1, 0],
        [0, 1],
        [1, 0],
    ]

    with pytest.raises((ValueError, ZeroDivisionError)):
        fleiss_kappa(ratings)


def test_fleiss_kappa_rejects_inconsistent_rating_counts():
    ratings = [
        [2, 0],
        [0, 3],
    ]

    with pytest.raises(ValueError):
        fleiss_kappa(ratings)


def test_gold_accuracy_with_multiple_annotators():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
        {"item_id": "2", "annotator_id": "A", "label": "dog"},
        {"item_id": "1", "annotator_id": "B", "label": "cat"},
        {"item_id": "2", "annotator_id": "B", "label": "cat"},
    ]
    gold_items = {"1": "cat", "2": "cat"}

    result = gold_accuracy(annotations, gold_items)

    assert result["overall_accuracy"] == 0.75
    assert result["per_annotator"]["A"]["accuracy"] == 0.5
    assert result["per_annotator"]["B"]["accuracy"] == 1.0


def test_gold_accuracy_with_empty_annotations():
    result = gold_accuracy([], {"1": "cat"})

    assert result["overall_accuracy"] == 0.0
    assert result["per_annotator"] == {}


def test_gold_accuracy_with_empty_gold_items():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
    ]

    result = gold_accuracy(annotations, {})

    assert result["overall_accuracy"] == 0.0
    assert result["per_annotator"] == {}



def test_cohens_kappa_partial_agreement():
    labels_a = ["cat", "cat", "dog", "dog"]
    labels_b = ["cat", "dog", "dog", "dog"]

    assert cohens_kappa(labels_a, labels_b) == pytest.approx(0.5)


def test_cohens_kappa_complete_disagreement():
    labels_a = ["cat", "cat", "dog", "dog"]
    labels_b = ["dog", "dog", "cat", "cat"]

    assert cohens_kappa(labels_a, labels_b) == pytest.approx(-1.0)


def test_cohens_kappa_identical_single_category():
    labels_a = ["cat", "cat", "cat"]
    labels_b = ["cat", "cat", "cat"]

    assert cohens_kappa(labels_a, labels_b) == pytest.approx(1.0)


def test_fleiss_kappa_partial_agreement():
    ratings = [
        [2, 1],
        [1, 2],
        [2, 1],
    ]

    result = fleiss_kappa(ratings)

    assert result == pytest.approx(-0.35)

def test_fleiss_kappa_rejects_negative_counts():
    ratings = [
        [3, 0],
        [-1, 4],
    ]

    with pytest.raises(ValueError):
        fleiss_kappa(ratings)


def test_fleiss_kappa_rejects_fractional_counts():
    ratings = [
        [2.5, 0.5],
        [1.5, 1.5],
    ]

    with pytest.raises(ValueError):
        fleiss_kappa(ratings)


def test_fleiss_kappa_rejects_one_dimensional_input():
    import pytest
    from scoring.agreement.kappa import fleiss_kappa

    with pytest.raises(ValueError, match="two-dimensional"):
        fleiss_kappa([1, 2, 3])


def test_fleiss_kappa_rejects_single_category():
    import pytest
    from scoring.agreement.kappa import fleiss_kappa

    with pytest.raises(ValueError, match="at least two categories"):
        fleiss_kappa([[3]])


def test_fleiss_kappa_rejects_non_finite_counts():
    import pytest
    from scoring.agreement.kappa import fleiss_kappa

    with pytest.raises(ValueError, match="finite numbers"):
        fleiss_kappa([[float("nan"), 2], [1, 2]])


def test_fleiss_kappa_rejects_empty_matrix():
    import pytest
    from scoring.agreement.kappa import fleiss_kappa

    with pytest.raises(ValueError, match="must not be empty"):
        fleiss_kappa([])


def test_fleiss_kappa_returns_one_for_perfect_expected_agreement():
    from scoring.agreement.kappa import fleiss_kappa

    assert fleiss_kappa([[3, 0], [3, 0]]) == 1.0
