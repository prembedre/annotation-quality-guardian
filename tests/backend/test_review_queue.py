"""
Unit & integration tests for the Review Queue and
Item Resolution endpoints.
"""

from app.models import (
    Project,
    Item,
    Annotator,
    Annotation,
    TrustScore,
)


def create_trust_score(
    db_session,
    project_id,
    item_id,
    final_score,
    flagged,
):
    """Create a Phase 2 trust score for a test item."""

    trust_score = TrustScore(
        project_id=project_id,
        item_id=item_id,
        gold_score=final_score,
        agreement_score=final_score,
        behavioral_score=final_score,
        embedding_score=final_score,
        final_score=final_score,
        breakdown={
            "gold": final_score,
            "agreement": final_score,
            "behavioral": final_score,
            "embedding": final_score,
        },
        flagged=flagged,
    )

    db_session.add(trust_score)
    return trust_score


def test_review_queue_pagination_and_filtering(
    client,
    db_session,
):
    """Test review queue filtering and pagination."""

    project = Project(
        id=10,
        name="Review Project",
        label_set=["spam", "ham"],
    )

    annotator = Annotator(
        id=50,
        username="annotator50",
        email="annotator50@example.com",
    )

    db_session.add_all([project, annotator])
    db_session.commit()

    # Create 5 items:
    # 3 flagged and 2 normal.
    for i in range(1, 6):

        item = Item(
            project_id=10,
            external_id=f"doc_{i}",
            content={
                "text": f"Document text {i}",
            },
        )

        db_session.add(item)
        db_session.flush()

        annotation = Annotation(
            project_id=10,
            item_id=item.id,
            annotator_id=50,
            label="spam" if i % 2 == 0 else "ham",
            confidence=0.90,
        )

        db_session.add(annotation)

        is_flagged = i <= 3
        score_value = 0.35 if is_flagged else 0.95

        create_trust_score(
            db_session=db_session,
            project_id=10,
            item_id=item.id,
            final_score=score_value,
            flagged=is_flagged,
        )

    db_session.commit()

    # ---------------------------------------------------------
    # 1. Fetch only flagged items
    # ---------------------------------------------------------

    response = client.get(
        "/api/review/queue"
        "?project_id=10"
        "&flagged=true"
        "&page=1"
        "&page_size=10"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["total_pages"] == 1

    # ---------------------------------------------------------
    # 2. Test pagination
    # ---------------------------------------------------------

    response_paged = client.get(
        "/api/review/queue"
        "?project_id=10"
        "&flagged=true"
        "&page=1"
        "&page_size=2"
    )

    assert response_paged.status_code == 200

    data_paged = response_paged.json()

    assert len(data_paged["items"]) == 2
    assert data_paged["total"] == 3
    assert data_paged["total_pages"] == 2

    # ---------------------------------------------------------
    # 3. Test score threshold filter
    # ---------------------------------------------------------

    response_score = client.get(
        "/api/review/queue"
        "?project_id=10"
        "&max_score=0.5"
    )

    assert response_score.status_code == 200

    score_data = response_score.json()

    assert score_data["total"] == 3


def test_resolve_review_item(client, db_session):
    """Test resolving a flagged review item."""

    project = Project(
        id=11,
        name="Resolve Project",
        label_set=["pos", "neg"],
    )

    item = Item(
        project_id=11,
        external_id="item_resolve_test",
        content={
            "text": "Ambiguous input",
        },
    )

    db_session.add_all([project, item])
    db_session.commit()

    trust_score = create_trust_score(
        db_session=db_session,
        project_id=11,
        item_id=item.id,
        final_score=0.25,
        flagged=True,
    )

    db_session.commit()

    # ---------------------------------------------------------
    # Resolve the item
    # ---------------------------------------------------------

    response = client.post(
        f"/api/review/{item.id}/resolve",
        json={
            "ground_truth_label": "pos",
            "notes": "Audited by Senior Reviewer",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["status"] == "resolved"
    assert data["gold_label"] == "pos"

    # ---------------------------------------------------------
    # Verify Item
    # ---------------------------------------------------------

    db_session.refresh(item)

    assert item.is_gold is True
    assert item.gold_label == "pos"

    # ---------------------------------------------------------
    # Verify TrustScore
    # ---------------------------------------------------------

    db_session.refresh(trust_score)

    assert trust_score.flagged is False
    assert (
        trust_score.breakdown.get("resolved_gold_label")
        == "pos"
    )


def test_resolve_nonexistent_item(client):
    """Test resolving an item that does not exist."""

    response = client.post(
        "/api/review/99999/resolve",
        json={
            "ground_truth_label": "positive",
        },
    )

    assert response.status_code == 404
