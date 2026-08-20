import pytest
from unittest.mock import patch, MagicMock
from app.models import Project, Annotator, Item
from app.celery_app import celery_app


@pytest.fixture(autouse=True)
def setup_eager_celery():
    """Ensure Celery tasks execute synchronously during job API tests."""
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = original_eager


def test_submit_behavioral_job(client, db_session):
    """Test submitting an async behavioral scoring job."""
    project = Project(id=301, name="Job Project 1", label_set=["A", "B"])
    annotator = Annotator(id=401, username="job_ann_1")
    db_session.add_all([project, annotator])
    db_session.commit()

    response = client.post(
        "/api/jobs/behavioral",
        json={
            "project_id": 301,
            "annotator_id": 401,
            "anomaly_score": 0.75,
            "anomaly_flag": True,
            "reason": "Abnormal timing",
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in {"PENDING", "COMPLETED", "RUNNING"}


def test_submit_embedding_job(client, db_session):
    """Test submitting an async embedding analysis job."""
    project = Project(id=302, name="Job Project 2", label_set=["X", "Y"])
    db_session.add(project)
    db_session.commit()

    response = client.post(
        "/api/jobs/embedding",
        json={
            "project_id": 302,
            "model_name": "text-embedding-3-small",
            "outlier_threshold": 0.80,
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in {"PENDING", "COMPLETED", "RUNNING"}


def test_submit_trust_score_job(client, db_session):
    """Test submitting an async unified trust score job."""
    project = Project(id=303, name="Job Project 3", label_set=["1", "2"])
    db_session.add(project)
    db_session.commit()

    response = client.post(
        "/api/jobs/trust-score",
        json={
            "project_id": 303,
            "weights": {
                "gold": 0.4,
                "agreement": 0.3,
                "behavioral": 0.15,
                "embedding": 0.15,
            },
        },
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data


def test_get_job_status(client):
    """Test polling job status endpoint."""
    with patch("app.api.jobs.AsyncResult") as mock_async_result:
        mock_instance = MagicMock()
        mock_instance.status = "SUCCESS"
        mock_instance.successful.return_value = True
        mock_instance.failed.return_value = False
        mock_instance.ready.return_value = True
        mock_instance.result = {"status": "COMPLETED", "items_processed": 5}
        mock_async_result.return_value = mock_instance

        response = client.get("/api/jobs/fake-job-uuid-123")
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "fake-job-uuid-123"
        assert data["status"] == "COMPLETED"
        assert data["result_available"] is True
        assert data["result"]["items_processed"] == 5
