from datetime import datetime, timedelta

from scoring.automation.underperformer import detect_underperformers


def make_annotation(item_id, annotator_id, label, created_at):
    return {
        "item_id": item_id,
        "annotator_id": annotator_id,
        "label": label,
        "created_at": created_at,
    }


def make_trust_score(item_id, final_score):
    return {
        "item_id": item_id,
        "final_score": final_score,
    }


def test_detects_low_accuracy_underperformer():
    as_of = datetime(2026, 9, 8)

    gold_items = {f"item-{i}": "Positive" for i in range(10)}

    annotations = [
        make_annotation(
            f"item-{i}",
            1,
            "Negative" if i < 4 else "Positive",
            as_of - timedelta(days=i),
        )
        for i in range(10)
    ]

    trust_scores = [
        make_trust_score(f"item-{i}", 0.80)
        for i in range(10)
    ]

    results = detect_underperformers(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        gold_threshold=0.90,
        trust_threshold=0.60,
        minimum_annotations=10,
        window_days=30,
        as_of=as_of,
    )

    assert len(results) == 1
    result = results[0]

    assert result.annotator_id == "1"
    assert result.total_annotations == 10
    assert result.rolling_accuracy == 0.60
    assert result.gold_correct == 6
    assert result.gold_annotations == 10
    assert result.average_trust_score == 0.80
    assert result.underperforming is True
    assert any("Rolling accuracy" in reason for reason in result.reasons)


def test_detects_low_trust_underperformer():
    as_of = datetime(2026, 9, 8)

    gold_items = {f"item-{i}": "Positive" for i in range(10)}

    annotations = [
        make_annotation(
            f"item-{i}",
            2,
            "Positive",
            as_of - timedelta(days=i),
        )
        for i in range(10)
    ]

    trust_scores = [
        make_trust_score(f"item-{i}", 0.40)
        for i in range(10)
    ]

    results = detect_underperformers(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        gold_threshold=0.90,
        trust_threshold=0.60,
        minimum_annotations=10,
        window_days=30,
        as_of=as_of,
    )

    assert len(results) == 1
    result = results[0]

    assert result.annotator_id == "2"
    assert result.total_annotations == 10
    assert result.rolling_accuracy == 1.0
    assert result.average_trust_score == 0.40
    assert result.underperforming is True
    assert any("Average trust score" in reason for reason in result.reasons)


def test_does_not_flag_insufficient_history():
    as_of = datetime(2026, 9, 8)

    gold_items = {f"item-{i}": "Positive" for i in range(5)}

    annotations = [
        make_annotation(
            f"item-{i}",
            3,
            "Negative",
            as_of - timedelta(days=i),
        )
        for i in range(5)
    ]

    trust_scores = [
        make_trust_score(f"item-{i}", 0.30)
        for i in range(5)
    ]

    results = detect_underperformers(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        minimum_annotations=10,
        window_days=30,
        as_of=as_of,
    )

    assert len(results) == 1
    result = results[0]

    assert result.annotator_id == "3"
    assert result.total_annotations == 5
    assert result.underperforming is False
    assert result.reasons == []


def test_ignores_annotations_outside_rolling_window():
    as_of = datetime(2026, 9, 8)

    gold_items = {f"item-{i}": "Positive" for i in range(10)}

    annotations = [
        make_annotation(
            f"item-{i}",
            4,
            "Negative",
            as_of - timedelta(days=60),
        )
        for i in range(10)
    ]

    trust_scores = [
        make_trust_score(f"item-{i}", 0.30)
        for i in range(10)
    ]

    results = detect_underperformers(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        minimum_annotations=10,
        window_days=30,
        as_of=as_of,
    )

    assert results == []
