import pytest
from unittest.mock import patch, MagicMock
from app.models import Project, Annotator, Item
from app.celery_app import celery_app
from app.core.config import settings, EnvironmentType


@pytest.fixture(autouse=True)
def setup_eager_celery():
    """Ensure Celery tasks execute synchronously during job API tests."""
    original_eager = celery_app.conf.task_always_eager
    celery_app.conf.task_always_eager = True
    yield
    celery_app.conf.task_always_eager = original_eager


def test_submit_behavioral_job(client, db_session, admin_headers):
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
        headers=admin_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in {"PENDING", "COMPLETED", "RUNNING"}


def test_submit_embedding_job(client, db_session, admin_headers):
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
        headers=admin_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] in {"PENDING", "COMPLETED", "RUNNING"}


def test_submit_trust_score_job(client, db_session, admin_headers):
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
        headers=admin_headers,
    )

    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data


def test_get_job_status(client, admin_headers):
    """Test polling job status endpoint."""
    with patch("app.api.jobs.AsyncResult") as mock_async_result:
        mock_instance = MagicMock()
        mock_instance.status = "SUCCESS"
        mock_instance.successful.return_value = True
        mock_instance.failed.return_value = False
        mock_instance.ready.return_value = True
        mock_instance.result = {"status": "COMPLETED", "items_processed": 5}
        mock_async_result.return_value = mock_instance

        response = client.get("/api/jobs/fake-job-uuid-123", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "fake-job-uuid-123"
        assert data["status"] == "COMPLETED"
        assert data["result_available"] is True
        assert data["result"]["items_processed"] == 5


def test_jobs_unauthenticated_returns_401(client):
    """Unauthenticated job trigger returns 401."""
    response = client.post(
        "/api/jobs/behavioral",
        json={"project_id": 1, "annotator_id": 1, "anomaly_score": 0.5},
    )
    assert response.status_code == 401


def test_jobs_insufficient_role_returns_403(client, annotator_headers):
    """Annotator role cannot trigger background compute jobs."""
    response = client.post(
        "/api/jobs/behavioral",
        json={"project_id": 1, "annotator_id": 1, "anomaly_score": 0.5},
        headers=annotator_headers,
    )
    assert response.status_code == 403


def test_job_submission_redis_down_returns_503(client, admin_headers, db_session):
    """When Redis is down and in production mode, returns 503 Service Unavailable."""
    project = Project(id=990, name="Redis Down Test", label_set=["A", "B"])
    annotator = Annotator(id=991, username="ann_down")
    db_session.add_all([project, annotator])
    db_session.commit()

    with patch("app.tasks.behavioral_tasks.compute_behavioral_score_task.apply_async", side_effect=ConnectionError("Cannot connect to redis://localhost:6379")):
        with patch.object(settings, "ENV", EnvironmentType.PRODUCTION):
            response = client.post(
                "/api/jobs/behavioral",
                json={
                    "project_id": 990,
                    "annotator_id": 991,
                    "anomaly_score": 0.5,
                },
                headers=admin_headers,
            )
            assert response.status_code == 503
            assert "Redis" in response.json()["detail"]
            assert "unreachable" in response.json()["detail"]


def test_job_submission_redis_down_dev_fallback_to_eager(client, admin_headers, db_session):
    """When Redis is down in dev mode, falls back to eager execution without hanging."""
    project = Project(id=992, name="Redis Fallback Test", label_set=["A", "B"])
    annotator = Annotator(id=993, username="ann_eager")
    db_session.add_all([project, annotator])
    db_session.commit()

    with patch("app.tasks.behavioral_tasks.compute_behavioral_score_task.apply_async", side_effect=ConnectionError("Redis connection refused")):
        with patch.object(settings, "ENV", EnvironmentType.DEVELOPMENT):
            response = client.post(
                "/api/jobs/behavioral",
                json={
                    "project_id": 992,
                    "annotator_id": 993,
                    "anomaly_score": 0.3,
                },
                headers=admin_headers,
            )
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            assert data["status"] in {"COMPLETED", "PENDING"}
