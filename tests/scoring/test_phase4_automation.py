from datetime import datetime, timedelta

from scoring.phase4 import (
    build_ab_test_analytics,
    build_ambiguity_analytics,
    build_rerouting_recommendation,
    build_underperformer_analytics,
)


def test_underperformer_detection():
    annotations = [
        {
            "item_id": f"item-{i}",
            "annotator_id": "1",
            "label": "wrong" if i < 4 else "correct",
            "created_at": datetime(2026, 9, 8),
        }
        for i in range(10)
    ]

    gold_items = {
        f"item-{i}": "correct"
        for i in range(10)
    }

    trust_scores = [
        {
            "item_id": f"item-{i}",
            "final_score": 0.80,
        }
        for i in range(10)
    ]

    results = build_underperformer_analytics(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        minimum_annotations=10,
    )

    assert len(results) == 1
    assert results[0].annotator_id == "1"
    assert results[0].rolling_accuracy == 0.60
    assert results[0].underperforming is True


def test_rerouting_recommendation():
    performance = [
        {
            "annotator_id": "1",
            "rolling_accuracy": 0.50,
            "average_trust_score": 0.40,
            "underperforming": True,
        },
        {
            "annotator_id": "2",
            "rolling_accuracy": 0.93,
            "average_trust_score": 0.80,
            "underperforming": False,
        },
        {
            "annotator_id": "3",
            "rolling_accuracy": 0.97,
            "average_trust_score": 0.91,
            "underperforming": False,
        },
    ]

    result = build_rerouting_recommendation(
        item_id="item-101",
        original_annotator_id="1",
        annotator_performance=performance,
    )

    assert result.recommended_annotator_id == "3"
    assert result.recommendation_score == 0.97


def test_ab_testing_recommends_better_schema():
    annotations = [
        {
            "item_id": "item-1",
            "annotator_id": "1",
            "label": "yes",
            "metadata": {"schema_version": "A"},
        },
        {
            "item_id": "item-2",
            "annotator_id": "1",
            "label": "yes",
            "metadata": {"schema_version": "A"},
        },
        {
            "item_id": "item-3",
            "annotator_id": "1",
            "label": "yes",
            "metadata": {"schema_version": "B"},
        },
        {
            "item_id": "item-4",
            "annotator_id": "1",
            "label": "no",
            "metadata": {"schema_version": "B"},
        },
    ]

    gold_items = {
        "item-1": "yes",
        "item-2": "yes",
        "item-3": "yes",
        "item-4": "yes",
    }

    result = build_ab_test_analytics(
        experiment_name="label-schema-test",
        annotations=annotations,
        gold_items=gold_items,
    )

    assert result.variant_a.accuracy == 1.0
    assert result.variant_b.accuracy == 0.5
    assert result.recommended_variant == "A"


def test_ambiguous_class_detection():
    annotations = []

    # Five items where annotators disagree about the "uncertain" class.
    for i in range(5):
        annotations.extend(
            [
                {
                    "item_id": f"item-{i}",
                    "annotator_id": "1",
                    "label": "uncertain",
                },
                {
                    "item_id": f"item-{i}",
                    "annotator_id": "2",
                    "label": "clear",
                },
            ]
        )

    results = build_ambiguity_analytics(
        annotations=annotations,
        disagreement_threshold=0.50,
        minimum_comparisons=5,
    )

    uncertain = next(
        result
        for result in results
        if result.label == "uncertain"
    )

    assert uncertain.ambiguous is True
    assert uncertain.disagreements == 5
    assert uncertain.disagreement_rate == 1.0