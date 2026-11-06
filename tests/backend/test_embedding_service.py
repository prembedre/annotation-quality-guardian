"""
Unit tests for Embedding Outlier Integration Service.
"""

from app.models import Project, Item, EmbeddingResult
from app.services.embedding_service import (
    record_embedding_result,
    get_embedding_results_by_project,
    get_embedding_result_for_item,
    compute_project_embedding_outliers,
)
from scoring.embeddings import compute_tfidf_outlier_scores


def test_record_and_query_embedding_result(db_session):
    """Test storing, querying, and filtering embedding outlier results."""
    project = Project(id=220, name="Embedding Service Test", label_set=["A", "B"])
    item1 = Item(id=701, project_id=220, external_id="embed_item_1", content={"text": "normal"})
    item2 = Item(id=702, project_id=220, external_id="embed_item_2", content={"text": "gibberish"})
    db_session.add_all([project, item1, item2])
    db_session.commit()

    # Inlier item
    res1 = record_embedding_result(
        db=db_session,
        project_id=220,
        item_id=701,
        model_name="test-model",
        outlier_score=0.12,
        is_outlier=False,
        embedding=[0.1, 0.2],
    )
    assert res1.id is not None
    assert float(res1.outlier_score) == 0.12
    assert res1.is_outlier is False

    # Outlier item
    res2 = record_embedding_result(
        db=db_session,
        project_id=220,
        item_id=702,
        model_name="test-model",
        outlier_score=0.95,
        is_outlier=True,
        embedding=[-0.9, -0.8],
        nearest_item_id=701,
    )
    assert res2.id is not None
    assert float(res2.outlier_score) == 0.95
    assert res2.is_outlier is True

    # Query item result
    item_res = get_embedding_result_for_item(db=db_session, project_id=220, item_id=702)
    assert item_res is not None
    assert item_res.is_outlier is True

    # Filter outliers only
    outliers = get_embedding_results_by_project(db=db_session, project_id=220, outliers_only=True)
    assert len(outliers) == 1
    assert outliers[0].item_id == 702


def test_compute_tfidf_outlier_scores():
    items = [
        {"item_id": 1, "content": {"text": "customer service was great and helpful"}, "label": "positive"},
        {"item_id": 2, "content": {"text": "wonderful service and great experience"}, "label": "positive"},
        {"item_id": 3, "content": {"text": "excellent customer support and friendly staff"}, "label": "positive"},
        # Outlier item in a customer service context
        {"item_id": 4, "content": {"text": "astrophysics black hole gravitational quantum singularity"}, "label": "positive"},
    ]

    results = compute_tfidf_outlier_scores(items, outlier_threshold=0.60)
    assert len(results) == 4

    outlier_item = next(r for r in results if r["item_id"] == 4)
    inlier_item = next(r for r in results if r["item_id"] == 1)

    # Outlier should have higher outlier score than inliers
    assert outlier_item["outlier_score"] > inlier_item["outlier_score"]
    assert outlier_item["is_outlier"] is True

    # 2D projection coordinates exist and have 2 dimensions
    for r in results:
        assert len(r["embedding"]) == 2
        assert isinstance(r["embedding"][0], float)
        assert isinstance(r["embedding"][1], float)


def test_compute_project_embedding_outliers_database(db_session):
    proj = Project(name="Project Real Embeddings Test", label_set=["pos", "neg"])
    db_session.add(proj)
    db_session.commit()

    # Normal items
    items = [
        Item(project_id=proj.id, external_id="emb_1", content={"text": "happy with good product"}, gold_label="pos"),
        Item(project_id=proj.id, external_id="emb_2", content={"text": "great quality good product"}, gold_label="pos"),
        Item(project_id=proj.id, external_id="emb_3", content={"text": "very good product and quality"}, gold_label="pos"),
        # Outlier item
        Item(project_id=proj.id, external_id="emb_4", content={"text": "unrelated alien spacecraft warp drive"}, gold_label="pos"),
    ]
    db_session.add_all(items)
    db_session.commit()

    summary = compute_project_embedding_outliers(
        db=db_session,
        project_id=proj.id,
        outlier_threshold=0.60,
    )
    assert summary["items_processed"] == 4
    assert summary["outliers_detected"] >= 1

    stored_outliers = get_embedding_results_by_project(db_session, proj.id, outliers_only=True)
    assert len(stored_outliers) >= 1
    outlier_res = stored_outliers[0]
    assert outlier_res.is_outlier is True
    assert len(outlier_res.embedding) == 2
    assert outlier_res.nearest_item_id is not None

