"""
Automation Service.

Manages persistent project-level automation policies and rule enforcement.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.automation_rule import AutomationRule
from app.models.project import Project


DEFAULT_RULES = [
    {
        "rule_id": "rule-1",
        "title": "Low Trust Score Escalation",
        "condition": "Annotator Trust Score < 60% AND Confidence < 70%",
        "action": "Reassign automatically to Senior Tier (Annotator #3)",
        "active": True,
    },
    {
        "rule_id": "rule-2",
        "title": "Taxonomy Ambiguity Consensus",
        "condition": "Class Disagreement Rate > 20% on Ambiguous Classes",
        "action": "Require 2x Overlapping Annotator Verification",
        "active": True,
    },
    {
        "rule_id": "rule-3",
        "title": "Latent Space Outlier Quarantine",
        "condition": "Embedding Cosine Distance > 0.80 from Centroid",
        "action": "Route directly to Expert Review Queue",
        "active": False,
    },
]


def ensure_default_rules(db: Session, project_id: int) -> List[AutomationRule]:
    """
    Ensure the 3 standard automation rules exist for the specified project.
    """
    existing = (
        db.query(AutomationRule)
        .filter(AutomationRule.project_id == project_id)
        .all()
    )
    existing_map = {r.rule_id: r for r in existing}

    created = False
    for r_def in DEFAULT_RULES:
        if r_def["rule_id"] not in existing_map:
            rule = AutomationRule(
                project_id=project_id,
                rule_id=r_def["rule_id"],
                title=r_def["title"],
                condition=r_def["condition"],
                action=r_def["action"],
                active=r_def["active"],
            )
            db.add(rule)
            created = True

    if created:
        db.commit()
        existing = (
            db.query(AutomationRule)
            .filter(AutomationRule.project_id == project_id)
            .all()
        )

    return sorted(existing, key=lambda r: r.rule_id)


def get_project_automation_rules(
    db: Session,
    project_id: int,
) -> List[Dict[str, Any]]:
    """
    Retrieve all automation rules for a project, initializing defaults if needed.
    """
    rules = ensure_default_rules(db, project_id)
    return [
        {
            "id": r.rule_id,
            "rule_id": r.rule_id,
            "project_id": r.project_id,
            "title": r.title,
            "condition": r.condition,
            "action": r.action,
            "active": r.active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None,
        }
        for r in rules
    ]


def get_automation_rules_map(
    db: Session,
    project_id: Optional[int] = None,
) -> Dict[str, bool]:
    """
    Retrieve a mapping of rule_id -> active boolean for fast enforcement lookup.
    """
    if project_id is None:
        return {r["rule_id"]: r["active"] for r in DEFAULT_RULES}

    rules = ensure_default_rules(db, project_id)
    return {r.rule_id: r.active for r in rules}


def update_automation_rule(
    db: Session,
    project_id: int,
    rule_id: str,
    active: bool,
) -> Dict[str, Any]:
    """
    Update the active state of an automation rule for a project.
    """
    ensure_default_rules(db, project_id)

    rule = (
        db.query(AutomationRule)
        .filter(
            AutomationRule.project_id == project_id,
            AutomationRule.rule_id == rule_id,
        )
        .first()
    )

    if not rule:
        raise ValueError(f"Automation rule '{rule_id}' not found for project {project_id}")

    rule.active = bool(active)
    db.commit()
    db.refresh(rule)

    return {
        "id": rule.rule_id,
        "rule_id": rule.rule_id,
        "project_id": rule.project_id,
        "title": rule.title,
        "condition": rule.condition,
        "action": rule.action,
        "active": rule.active,
        "updated_at": rule.updated_at.isoformat() if rule.updated_at else None,
    }
