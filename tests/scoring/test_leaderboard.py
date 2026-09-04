from datetime import datetime, timedelta

from scoring.leaderboard.service import (
    calculate_leaderboard,
    calculate_rolling_accuracy,
)


def test_calculate_rolling_accuracy():
    now = datetime.now()

    annotations = [
        {
            "item_id": "1",
            "annotator_id": "A",
            "label": "cat",
            "created_at": now,
        },
        {
            "item_id": "2",
            "annotator_id": "A",
            "label": "dog",
            "created_at": now,
        },
        {
            "item_id": "3",
            "annotator_id": "B",
            "label": "cat",
            "created_at": now,
        },
    ]

    gold_items = {
        "1": "cat",
        "2": "cat",
        "3": "cat",
    }

    result = calculate_rolling_accuracy(
        annotations,
        gold_items,
        window_days=30,
        as_of=now,
    )

    assert result["A"]["accuracy"] == 0.5
    assert result["A"]["correct"] == 1
    assert result["A"]["total"] == 2

    assert result["B"]["accuracy"] == 1.0


def test_old_annotations_are_excluded_from_rolling_accuracy():
    now = datetime.now()

    annotations = [
        {
            "item_id": "1",
            "annotator_id": "A",
            "label": "wrong",
            "created_at": now - timedelta(days=60),
        },
        {
            "item_id": "2",
            "annotator_id": "A",
            "label": "cat",
            "created_at": now,
        },
    ]

    gold_items = {
        "1": "cat",
        "2": "cat",
    }

    result = calculate_rolling_accuracy(
        annotations,
        gold_items,
        window_days=30,
        as_of=now,
    )

    assert result["A"]["accuracy"] == 1.0
    assert result["A"]["correct"] == 1
    assert result["A"]["total"] == 1


def test_leaderboard_ranks_and_flags_annotators():
    now = datetime.now()

    annotations = [
        {
            "item_id": "1",
            "annotator_id": "A",
            "label": "cat",
            "created_at": now,
        },
        {
            "item_id": "2",
            "annotator_id": "A",
            "label": "dog",
            "created_at": now,
        },
        {
            "item_id": "3",
            "annotator_id": "B",
            "label": "cat",
            "created_at": now,
        },
    ]

    gold_items = {
        "1": "cat",
        "2": "cat",
        "3": "cat",
    }

    result = calculate_leaderboard(
        annotations,
        gold_items,
        gold_threshold=0.90,
        window_days=30,
        as_of=now,
    )

    leaderboard = result["leaderboard"]

    assert result["total_annotators"] == 2

    assert leaderboard[0]["annotator_id"] == "B"
    assert leaderboard[0]["rank"] == 1
    assert leaderboard[0]["rolling_accuracy"] == 1.0
    assert leaderboard[0]["flagged"] is False

    assert leaderboard[1]["annotator_id"] == "A"
    assert leaderboard[1]["rank"] == 2
    assert leaderboard[1]["rolling_accuracy"] == 0.5
    assert leaderboard[1]["flagged"] is True