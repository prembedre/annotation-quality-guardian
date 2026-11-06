"""
Tests for Automation Rules API and enforcement.
"""

import pytest
from app.models.annotation import Annotation
from app.models.annotator import Annotator
from app.models.item import Item
from app.models.project import Project
from app.models.trust_score import TrustScore
from app.services.automation_service import (
    get_automation_rules_map,
    get_project_automation_rules,
    update_automation_rule,
)
from app.services.rerouting_service import get_pending_reroutes
from app.services.trust_score_service import calculate_trust_score


def test_automation_rules_auth_required(client):
    res = client.get("/api/automation/rules")
    assert res.status_code == 401


def test_automation_rules_crud(client, db_session, admin_headers):
    project = Project(
        name="Automation Rules Test Project",
        label_set=["A", "B"],
        automation_enabled=True,
    )
    db_session.add(project)
    db_session.commit()

    # 1. GET rules returns 3 default rules
    res = client.get(
        f"/api/automation/rules?project_id={project.id}",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 3
    rule_ids = {r["rule_id"] for r in data}
    assert rule_ids == {"rule-1", "rule-2", "rule-3"}

    # Rule 3 is initially inactive
    rule3 = next(r for r in data if r["rule_id"] == "rule-3")
    assert rule3["active"] is False

    # 2. PUT toggles rule-3 to active
    put_res = client.put(
        f"/api/automation/rules/rule-3?project_id={project.id}",
        json={"active": True},
        headers=admin_headers,
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["rule_id"] == "rule-3"
    assert updated["active"] is True

    # 3. GET reflects persisted active state
    res2 = client.get(
        f"/api/automation/rules?project_id={project.id}",
        headers=admin_headers,
    )
    data2 = res2.json()
    rule3_after = next(r for r in data2 if r["rule_id"] == "rule-3")
    assert rule3_after["active"] is True


def test_automation_rule_1_low_trust_escalation_enforcement(db_session):
    project = Project(
        name="Escalation Enforcement Project",
        label_set=["A", "B"],
        automation_enabled=True,
    )
    db_session.add(project)
    db_session.flush()

    item = Item(project_id=project.id, external_id="esc-item-1", content={"text": "Escalation sample"})
    db_session.add(item)
    db_session.flush()

    # Low trust score item
    ts = TrustScore(
        project_id=project.id,
        item_id=item.id,
        final_score=0.45,
        score=0.45,
        flagged=True,
    )
    db_session.add(ts)
    db_session.commit()

    # With default rule-1 active -> item is included in pending reroutes
    pending = get_pending_reroutes(db=db_session, project_id=project.id)
    assert pending.total == 1
    assert pending.items[0].item_id == item.id

    # Toggle rule-1 off
    update_automation_rule(db=db_session, project_id=project.id, rule_id="rule-1", active=False)

    # Now pending reroutes excludes low-trust items
    pending_after = get_pending_reroutes(db=db_session, project_id=project.id)
    assert pending_after.total == 0


def test_automation_rule_3_outlier_quarantine_enforcement():
    # Outlier quarantine disabled (rule-3 = False):
    _, _, flagged_inactive, reason_inactive = calculate_trust_score(
        gold_score=0.95,
        agreement_score=0.95,
        behavioral_score=0.95,
        embedding_score=0.15,
        is_outlier=True,
        outlier_quarantine_enabled=False,
    )
    assert "quarantined" not in (reason_inactive or "")

    # Outlier quarantine enabled (rule-3 = True):
    _, _, flagged_active, reason_active = calculate_trust_score(
        gold_score=0.95,
        agreement_score=0.95,
        behavioral_score=0.95,
        embedding_score=0.15,
        is_outlier=True,
        outlier_quarantine_enabled=True,
    )
    assert flagged_active is True
    assert "quarantined" in (reason_active or "")
