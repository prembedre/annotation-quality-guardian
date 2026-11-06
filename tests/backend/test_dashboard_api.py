"""
Tests for Dashboard API endpoints (trend telemetry, leaderboard, heatmap).
"""

import pytest
from app.models.annotation import Annotation
from app.models.annotator import Annotator
from app.models.item import Item
from app.models.project import Project
from app.models.trust_score import TrustScore


def test_dashboard_trend_auth_required(client):
    res = client.get("/api/dashboard/trend")
    assert res.status_code == 401


def test_dashboard_trend_empty_project(client, db_session, admin_headers):
    project = Project(name="Empty Trend Project", label_set=["A", "B"])
    db_session.add(project)
    db_session.commit()

    res = client.get(
        f"/api/dashboard/trend?project_id={project.id}",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project.id
    assert data["is_empty"] is True
    assert data["points"] == []


def test_dashboard_trend_with_data(client, db_session, admin_headers):
    project = Project(name="Active Trend Project", label_set=["Positive", "Negative"])
    db_session.add(project)
    db_session.flush()

    item1 = Item(project_id=project.id, external_id="tr-item-1", content={"text": "T1"})
    item2 = Item(project_id=project.id, external_id="tr-item-2", content={"text": "T2"})
    ann1 = Annotator(name="Annotator 1")
    ann2 = Annotator(name="Annotator 2")
    db_session.add_all([item1, item2, ann1, ann2])
    db_session.flush()

    a1 = Annotation(item_id=item1.id, annotator_id=ann1.id, project_id=project.id, label="Positive")
    a2 = Annotation(item_id=item1.id, annotator_id=ann2.id, project_id=project.id, label="Positive")
    a3 = Annotation(item_id=item2.id, annotator_id=ann1.id, project_id=project.id, label="Negative")
    a4 = Annotation(item_id=item2.id, annotator_id=ann2.id, project_id=project.id, label="Negative")
    ts1 = TrustScore(project_id=project.id, item_id=item1.id, final_score=0.88, score=0.88)
    ts2 = TrustScore(project_id=project.id, item_id=item2.id, final_score=0.92, score=0.92)
    db_session.add_all([a1, a2, a3, a4, ts1, ts2])
    db_session.commit()

    for tr in ["24h", "7d", "30d"]:
        res = client.get(
            f"/api/dashboard/trend?project_id={project.id}&time_range={tr}",
            headers=admin_headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["project_id"] == project.id
        assert data["time_range"] == tr
        assert data["is_empty"] is False
        assert len(data["points"]) > 0
        assert data["current_trust"] == 90.0  # (0.88 + 0.92) / 2 * 100
        assert data["current_kappa"] == 100.0  # unanimous agreement
