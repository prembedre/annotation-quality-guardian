from scoring.agreement.heatmap import (
    calculate_disagreement_statistics,
    generate_agreement_heatmap,
)


def test_generate_agreement_heatmap():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
        {"item_id": "1", "annotator_id": "B", "label": "cat"},
        {"item_id": "2", "annotator_id": "A", "label": "dog"},
        {"item_id": "2", "annotator_id": "B", "label": "cat"},
    ]

    result = generate_agreement_heatmap(annotations)

    assert result["annotator_ids"] == ["A", "B"]
    assert result["matrix"] == [
        [1.0, 0.5],
        [0.5, 1.0],
    ]

    assert len(result["cells"]) == 4


def test_disagreement_statistics():
    annotations = [
        {"item_id": "1", "annotator_id": "A", "label": "cat"},
        {"item_id": "1", "annotator_id": "B", "label": "cat"},
        {"item_id": "2", "annotator_id": "A", "label": "dog"},
        {"item_id": "2", "annotator_id": "B", "label": "cat"},
    ]

    result = calculate_disagreement_statistics(annotations)

    assert len(result["disagreement_pairs"]) == 1

    pair = result["disagreement_pairs"][0]

    assert pair["item_id"] == "2"
    assert pair["annotator_a"] == "A"
    assert pair["annotator_b"] == "B"
    assert pair["label_a"] == "dog"
    assert pair["label_b"] == "cat"

    assert result["by_annotator"]["A"]["disagreements"] == 1
    assert result["by_annotator"]["B"]["disagreements"] == 1

    assert result["by_annotator"]["A"]["disagreement_rate"] == 0.5
    assert result["by_annotator"]["B"]["disagreement_rate"] == 0.5

    assert result["by_class"]["cat"]["disagreements"] == 1
    assert result["by_class"]["dog"]["disagreements"] == 1