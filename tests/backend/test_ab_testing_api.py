"""
Unit and API integration tests for A/B Testing Endpoints.
"""

import pytest
from app.models.project import Project
from app.models.item import Item
from app.models.annotator import Annotator
from app.models.annotation import Annotation
from app.models.ab_test_experiment import ABTestExperiment


def test_ab_testing_create_and_list(client, db_session, admin_headers):
    proj = Project(name="AB Test Project", label_set=["cat", "dog"])
    db_session.add(proj)
    db_session.commit()

    payload = {
        "project_id": proj.id,
        "experiment_name": "Guideline Clarification Test",
        "schema_version_a": {"description": "Baseline instructions"},
        "schema_version_b": {"description": "Revised with contrast examples", "labels": ["cat", "dog", "other"]},
        "annotator_group": {"allocation": "SPLIT_50_50"},
        "assigned_version": "SPLIT_50_50",
        "status": "active",
    }

    create_res = client.post("/api/ab-testing/experiments", json=payload, headers=admin_headers)
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["experiment_name"] == "Guideline Clarification Test"
    assert created["project_id"] == proj.id
    assert created["status"] == "active"

    # List experiments for project
    list_res = client.get(f"/api/ab-testing/experiments?project_id={proj.id}", headers=admin_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 1
    assert data["experiments"][0]["id"] == created["id"]


def test_ab_testing_promote_variant(client, db_session, admin_headers):
    proj = Project(name="Promote Variant Project", label_set=["pos", "neg"])
    db_session.add(proj)
    db_session.commit()

    exp = ABTestExperiment(
        project_id=proj.id,
        experiment_name="Promotion Trial",
        schema_version_a={"description": "Baseline"},
        schema_version_b={"description": "Winning Variant", "labels": ["pos", "neg", "neutral"]},
        assigned_version="SPLIT_50_50",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    # Promote Variant B
    promote_res = client.post(f"/api/ab-testing/experiments/{exp.id}/promote?variant=B", headers=admin_headers)
    assert promote_res.status_code == 200
    promoted = promote_res.json()
    assert promoted["status"] == "completed"
    assert promoted["assigned_version"] == "B"
    assert promoted["completed_at"] is not None

    # Project label set was updated from Variant B labels
    db_session.refresh(proj)
    assert "neutral" in proj.label_set


def test_ab_testing_results(client, db_session, admin_headers):
    proj = Project(name="Results Analytics Project", label_set=["cat", "dog"])
    db_session.add(proj)
    db_session.commit()

    exp = ABTestExperiment(
        project_id=proj.id,
        experiment_name="Analytics Experiment",
        schema_version_a={"version": "A"},
        schema_version_b={"version": "B"},
        assigned_version="SPLIT_50_50",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()

    # Create gold item and annotations
    item = Item(project_id=proj.id, external_id="gold-item-1", content={"text": "fluffy animal"}, is_gold=True, gold_label="cat")
    ann = Annotator(name="Evaluator")
    db_session.add_all([item, ann])
    db_session.commit()

    a1 = Annotation(
        project_id=proj.id,
        item_id=item.id,
        annotator_id=ann.id,
        label="cat",
        confidence=0.95,
        duration_ms=1200,
        metadata_={"variant": "B"},
    )
    db_session.add(a1)
    db_session.commit()

    results_res = client.get(f"/api/ab-testing/experiments/{exp.id}/results", headers=admin_headers)
    assert results_res.status_code == 200
    res_data = results_res.json()
    assert res_data["experiment_name"] == "Analytics Experiment"
    assert "variant_a" in res_data
    assert "variant_b" in res_data
