"""
Unit and integration tests for Projects API and Project Summaries.
"""

import pytest
from app.models.project import Project
from app.models.item import Item
from app.models.annotator import Annotator
from app.models.annotation import Annotation
from app.models.project_threshold import ProjectThreshold


def test_list_and_archive_projects(client, db_session, admin_headers):
    # Create test projects
    p1 = Project(name="Project Alpha", description="Active alpha", is_archived=False)
    p2 = Project(name="Project Beta", description="Archived beta", is_archived=True)
    db_session.add_all([p1, p2])
    db_session.commit()

    # Active projects only by default
    res = client.get("/api/projects", headers=admin_headers)
    assert res.status_code == 200
    names = [p["name"] for p in res.json()]
    assert "Project Alpha" in names
    assert "Project Beta" not in names

    # Include archived
    res_archived = client.get("/api/projects?include_archived=true", headers=admin_headers)
    assert res_archived.status_code == 200
    names_all = [p["name"] for p in res_archived.json()]
    assert "Project Alpha" in names_all
    assert "Project Beta" in names_all

    # Archive Project Alpha
    res_archive = client.post(f"/api/projects/{p1.id}/archive", headers=admin_headers)
    assert res_archive.status_code == 200
    assert res_archive.json()["is_archived"] is True

    # Unarchive Project Alpha
    res_unarchive = client.post(f"/api/projects/{p1.id}/unarchive", headers=admin_headers)
    assert res_unarchive.status_code == 200
    assert res_unarchive.json()["is_archived"] is False


def test_duplicate_project(client, db_session, admin_headers):
    project = Project(
        name="Clinical Trials NLP",
        description="Extract clinical entities",
        label_set=["disease", "treatment", "outcome"],
        automation_enabled=True,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # Attach threshold
    threshold = ProjectThreshold(
        project_id=project.id,
        gold_threshold=0.92,
        kappa_threshold=0.75,
        behavioral_threshold=0.80,
        embedding_threshold=0.85,
    )
    db_session.add(threshold)
    db_session.commit()

    # First duplicate
    res1 = client.post(f"/api/projects/{project.id}/duplicate", headers=admin_headers)
    assert res1.status_code == 201
    dup1 = res1.json()
    assert dup1["name"] == "Clinical Trials NLP (Copy)"
    assert dup1["automation_enabled"] is True
    assert dup1["label_set"] == ["disease", "treatment", "outcome"]

    # Verify duplicated threshold exists in DB
    dup1_threshold = (
        db_session.query(ProjectThreshold)
        .filter(ProjectThreshold.project_id == dup1["id"])
        .first()
    )
    assert dup1_threshold is not None
    assert float(dup1_threshold.gold_threshold) == pytest.approx(0.92)

    # Second duplicate creates (Copy 2)
    res2 = client.post(f"/api/projects/{project.id}/duplicate", headers=admin_headers)
    assert res2.status_code == 201
    dup2 = res2.json()
    assert dup2["name"] == "Clinical Trials NLP (Copy 2)"


def test_score_summary_real_metrics(client, db_session, annotator_headers):
    # Setup project with real items and annotations
    proj = Project(name="Summary Test Project", label_set=["cat", "dog"])
    db_session.add(proj)
    db_session.commit()

    it1 = Item(project_id=proj.id, external_id="ext-1", content={"text": "item 1"})
    it2 = Item(project_id=proj.id, external_id="ext-2", content={"text": "item 2"})
    db_session.add_all([it1, it2])

    ann1 = Annotator(name="Ann One")
    ann2 = Annotator(name="Ann Two")
    db_session.add_all([ann1, ann2])
    db_session.commit()

    a1 = Annotation(item_id=it1.id, annotator_id=ann1.id, project_id=proj.id, label="cat")
    a2 = Annotation(item_id=it1.id, annotator_id=ann2.id, project_id=proj.id, label="cat")
    a3 = Annotation(item_id=it2.id, annotator_id=ann1.id, project_id=proj.id, label="dog")
    a4 = Annotation(item_id=it2.id, annotator_id=ann2.id, project_id=proj.id, label="dog")
    db_session.add_all([a1, a2, a3, a4])
    db_session.commit()

    res = client.get(f"/api/scores/summary?project_id={proj.id}", headers=annotator_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_items"] == 2
    assert data["annotators_count"] == 2
    assert data["kappa"] is not None
    assert data["kappa"] == pytest.approx(1.0)
