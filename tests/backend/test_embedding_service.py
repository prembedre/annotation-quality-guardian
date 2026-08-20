"""
Unit tests for Embedding Outlier Integration Service.
"""

from app.models import Project, Item, EmbeddingResult
from app.services.embedding_service import (
    record_embedding_result,
    get_embedding_results_by_project,
    get_embedding_result_for_item,
)


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
