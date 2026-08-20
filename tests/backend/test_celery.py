"""
Unit tests for Celery configuration and background tasks.
"""

import pytest
from app.celery_app import celery_app, ping_task
from app.core.config import settings
from app.tasks.behavioral_tasks import compute_behavioral_score_task, process_batch_behavioral_task
from app.tasks.embedding_tasks import compute_embedding_outlier_task, process_project_embeddings_task
from app.tasks.trust_score_tasks import compute_project_trust_scores_task, compute_item_trust_score_task


@pytest.fixture(autouse=True)
def setup_eager_celery():
    """Ensure Celery tasks execute synchronously during unit tests."""
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = original_eager


def test_celery_configuration():
    """Verify Celery app loads settings and broker backend configuration."""
    assert celery_app.main == "annotation_quality_guardian"
    assert celery_app.conf.timezone == "UTC"
    assert celery_app.conf.task_serializer == "json"
    assert "redis" in settings.celery_broker.lower()
    assert "redis" in settings.celery_backend.lower()


def test_ping_task():
    """Verify simple verification ping task."""
    result = ping_task.delay()
    assert result.get() == "pong"


def test_behavioral_task_eager_execution(db_session):
    """Test behavioral anomaly task execution in eager mode."""
    from app.models import Project, Annotator
    proj = Project(id=101, name="Celery Behavioral Project", label_set=["A", "B"])
    ann = Annotator(id=201, username="celery_annotator")
    db_session.add_all([proj, ann])
    db_session.commit()

    task_res = compute_behavioral_score_task.delay(
        project_id=101,
        annotator_id=201,
        anomaly_score=0.85,
        anomaly_flag=True,
        reason="Speed anomaly detected",
    )
    res_data = task_res.get()
    assert res_data["status"] == "COMPLETED"
    assert res_data["project_id"] == 101
    assert res_data["annotator_id"] == 201
    assert res_data["anomaly_flag"] is True


def test_embedding_task_eager_execution(db_session):
    """Test embedding analysis task execution in eager mode."""
    from app.models import Project, Item
    proj = Project(id=102, name="Celery Embedding Project", label_set=["X", "Y"])
    item = Item(id=301, project_id=102, external_id="celery_item_1", content={"text": "Hello world"})
    db_session.add_all([proj, item])
    db_session.commit()

    task_res = compute_embedding_outlier_task.delay(
        project_id=102,
        item_id=301,
        model_name="test-embed-v1",
        outlier_score=0.92,
        is_outlier=True,
        embedding=[0.1, 0.2, 0.3],
    )
    res_data = task_res.get()
    assert res_data["status"] == "COMPLETED"
    assert res_data["item_id"] == 301
    assert res_data["is_outlier"] is True


def test_trust_score_task_eager_execution(db_session):
    """Test unified trust score task execution in eager mode."""
    from app.models import Project, Item
    proj = Project(id=103, name="Celery Trust Project", label_set=["1", "2"])
    item = Item(id=401, project_id=103, external_id="trust_item_1", content={"val": 42})
    db_session.add_all([proj, item])
    db_session.commit()

    task_res = compute_item_trust_score_task.delay(
        project_id=103,
        item_id=401,
    )
    res_data = task_res.get()
    assert res_data["status"] == "COMPLETED"
    assert res_data["item_id"] == 401
    assert "final_score" in res_data
