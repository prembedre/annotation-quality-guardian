"""
Seed demo data for Annotation Quality Guardian (AQG).
Populates:
- Project: Project 1 (AQG Demo Project)
- Annotators: Rahul, Prem, Venkatesh, Sidharth
- Sample Items & Annotations (agreement, disagreement, confidence, timestamps)
- Quality scores, Trust scores & Review queue items
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure paths
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.core.db import SessionLocal, engine
from app.core.db_patch import ensure_schema_compatibility
from app.models.project import Project
from app.models.project_threshold import ProjectThreshold
from app.models.annotator import Annotator
from app.models.item import Item
from app.models.annotation import Annotation
from app.models.trust_score import TrustScore
from app.models.reroute_history import RerouteHistory
from app.models.user import User, UserRole
from app.core.security import hash_password, verify_password
from app.services.trust_score_service import compute_and_save_item_trust_score

DEMO_USERS = [
    {
        "email": "admin@annotationops.io",
        "full_name": "Admin User",
        "role": UserRole.ADMIN,
        "password": "demo12345",
    },
    {
        "email": "pm@annotationops.io",
        "full_name": "Project Manager",
        "role": UserRole.PROJECT_MANAGER,
        "password": "demo12345",
    },
    {
        "email": "po@annotationops.io",
        "full_name": "Product Owner",
        "role": UserRole.PROJECT_MANAGER,
        "password": "demo12345",
    },
    {
        "email": "bob@annotationops.io",
        "full_name": "Reviewer Bob",
        "role": UserRole.REVIEWER,
        "password": "demo12345",
    },
    {
        "email": "dave@annotationops.io",
        "full_name": "Annotator Dave",
        "role": UserRole.ANNOTATOR,
        "password": "demo12345",
    },
    {
        "email": "sarah@annotationops.io",
        "full_name": "Annotator Sarah",
        "role": UserRole.ANNOTATOR,
        "password": "demo12345",
    },
]


def seed_demo_users(db=None):
    """Seed real platform users for demo accounts so RBAC is properly enforced."""
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        for u_data in DEMO_USERS:
            existing = db.query(User).filter(User.email == u_data["email"]).first()
            if not existing:
                user = User(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    hashed_password=hash_password(u_data["password"]),
                    role=u_data["role"],
                    is_active=True,
                )
                db.add(user)
            else:
                # Ensure existing demo user's password and active status are up-to-date
                if not verify_password(u_data["password"], existing.hashed_password):
                    existing.hashed_password = hash_password(u_data["password"])
                existing.is_active = True
                existing.role = u_data["role"]
        db.commit()
    finally:
        if close_db:
            db.close()


def seed_demo_data():
    ensure_schema_compatibility(engine)
    db = SessionLocal()

    try:
        print("[SEED] Seeding AQG Demo Data...")

        # 1. Project 1
        project = db.query(Project).filter(Project.id == 1).first()
        if not project:
            project = Project(
                id=1,
                name="Project 1",
                description="AQG Demo Project",
                label_set=["positive", "negative", "neutral"],
                automation_enabled=False,
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print("  * Created Project 1")
        else:
            project.name = "Project 1"
            project.description = "AQG Demo Project"
            project.label_set = ["positive", "negative", "neutral"]
            db.commit()
            print("  * Found existing Project 1")

        # 2. Project Thresholds
        threshold = db.query(ProjectThreshold).filter(ProjectThreshold.project_id == 1).first()
        if not threshold:
            threshold = ProjectThreshold(
                project_id=1,
                gold_threshold=0.90,
                kappa_threshold=0.70,
                behavioral_threshold=0.75,
                embedding_threshold=0.80,
                trust_threshold=0.60,
            )
            db.add(threshold)
            db.commit()
            print("  * Created Project 1 Thresholds")

        # 3. Annotators
        annotator_names = [
            ("Rahul", "rahul@example.com"),
            ("Prem", "prem@example.com"),
            ("Venkatesh", "venkatesh@example.com"),
            ("Sidharth", "sidharth@example.com"),
        ]

        annotators = {}
        for name, email in annotator_names:
            ann = (
                db.query(Annotator)
                .filter(
                    (Annotator.username == name) | (Annotator._name == name) | (Annotator.email == email)
                )
                .first()
            )
            if not ann:
                ann = Annotator(
                    username=name,
                    name=name,
                    email=email,
                )
                db.add(ann)
                db.commit()
                db.refresh(ann)
            annotators[name] = ann
            print(f"  * Annotator: {name} (id={ann.id})")

        # 4. Items (Mix of gold and non-gold)
        items_def = [
            # id, external_id, text, is_gold, gold_label
            (1, "item-001", "Outstanding service and quick response!", True, "positive"),
            (2, "item-002", "Defective item arrived, terrible support.", True, "negative"),
            (3, "item-003", "Package arrived on Wednesday as scheduled.", True, "neutral"),
            (4, "item-004", "Great value for money, exceeded expectations.", True, "positive"),
            (5, "item-005", "Completely useless, stopped working on day two.", True, "negative"),
            (6, "item-006", "Neutral tone, standard retail packaging.", False, None),
            (7, "item-007", "Ambiguous description, works fine but feels cheap.", False, None),
            (8, "item-008", "Exceptional customer experience, 5 stars!", False, None),
            (9, "item-009", "Never received product, seller ignored tickets.", False, None),
            (10, "item-010", "Average product, does what it says.", False, None),
        ]

        items = {}
        for item_id, ext_id, text_content, is_gold, gold_label in items_def:
            item = db.query(Item).filter(Item.project_id == 1, Item.external_id == ext_id).first()
            if not item:
                item = Item(
                    project_id=1,
                    external_id=ext_id,
                    source="default",
                    content={"text": text_content},
                    is_gold=is_gold,
                    gold_label=gold_label,
                )
                db.add(item)
                db.commit()
                db.refresh(item)
            items[ext_id] = item

        print(f"  * Seeded {len(items)} Items")

        # 5. Annotations (agreement, disagreement, confidences, durations)
        # We will create annotations for all 4 annotators across items
        base_time = datetime.now(timezone.utc) - timedelta(days=2)

        # Matrix of annotations: (ext_id, annotator_name, label, confidence, duration_ms, offset_hours)
        annotations_data = [
            # Item 1: High agreement on positive
            ("item-001", "Rahul", "positive", 0.96, 2400, 1),
            ("item-001", "Prem", "positive", 0.98, 2100, 2),
            ("item-001", "Venkatesh", "positive", 0.92, 2800, 3),
            ("item-001", "Sidharth", "positive", 0.89, 3200, 4),

            # Item 2: High agreement on negative
            ("item-002", "Rahul", "negative", 0.95, 2200, 5),
            ("item-002", "Prem", "negative", 0.99, 1900, 6),
            ("item-002", "Venkatesh", "negative", 0.91, 2600, 7),
            ("item-002", "Sidharth", "negative", 0.94, 2500, 8),

            # Item 3: Disagreement with gold neutral
            ("item-003", "Rahul", "neutral", 0.85, 3100, 9),
            ("item-003", "Prem", "neutral", 0.88, 3000, 10),
            ("item-003", "Venkatesh", "positive", 0.65, 4200, 11),  # disagreement
            ("item-003", "Sidharth", "positive", 0.62, 4500, 12),  # disagreement

            # Item 4: Agreement on positive
            ("item-004", "Rahul", "positive", 0.94, 2300, 13),
            ("item-004", "Prem", "positive", 0.97, 2000, 14),
            ("item-004", "Venkatesh", "positive", 0.88, 2900, 15),
            ("item-004", "Sidharth", "positive", 0.91, 2700, 16),

            # Item 5: Agreement on negative
            ("item-005", "Rahul", "negative", 0.93, 2500, 17),
            ("item-005", "Prem", "negative", 0.96, 2100, 18),
            ("item-005", "Venkatesh", "negative", 0.87, 3100, 19),
            ("item-005", "Sidharth", "negative", 0.89, 2800, 20),

            # Item 6: Neutral agreement
            ("item-006", "Rahul", "neutral", 0.82, 3300, 21),
            ("item-006", "Prem", "neutral", 0.86, 3200, 22),
            ("item-006", "Venkatesh", "neutral", 0.80, 3600, 23),
            ("item-006", "Sidharth", "neutral", 0.78, 3900, 24),

            # Item 7: High Disagreement / Flagged for Review Queue
            ("item-007", "Rahul", "neutral", 0.60, 4800, 25),
            ("item-007", "Prem", "negative", 0.72, 4100, 26),
            ("item-007", "Venkatesh", "positive", 0.55, 5200, 27),
            ("item-007", "Sidharth", "negative", 0.68, 4400, 28),

            # Item 8: Positive agreement
            ("item-008", "Rahul", "positive", 0.95, 2100, 29),
            ("item-008", "Prem", "positive", 0.98, 1800, 30),
            ("item-008", "Venkatesh", "positive", 0.90, 2600, 31),
            ("item-008", "Sidharth", "positive", 0.93, 2400, 32),

            # Item 9: Negative agreement
            ("item-009", "Rahul", "negative", 0.94, 2300, 33),
            ("item-009", "Prem", "negative", 0.97, 1900, 34),
            ("item-009", "Venkatesh", "negative", 0.86, 3000, 35),
            ("item-009", "Sidharth", "negative", 0.90, 2700, 36),

            # Item 10: Mild disagreement
            ("item-010", "Rahul", "neutral", 0.75, 3500, 37),
            ("item-010", "Prem", "neutral", 0.80, 3400, 38),
            ("item-010", "Venkatesh", "positive", 0.60, 4600, 39),
            ("item-010", "Sidharth", "neutral", 0.72, 3800, 40),
        ]

        added_annotations = 0
        for ext_id, ann_name, label, conf, dur, offset_h in annotations_data:
            item = items[ext_id]
            annotator = annotators[ann_name]

            existing_ann = (
                db.query(Annotation)
                .filter(
                    Annotation.project_id == 1,
                    Annotation.item_id == item.id,
                    Annotation.annotator_id == annotator.id,
                )
                .first()
            )

            if not existing_ann:
                ann = Annotation(
                    project_id=1,
                    item_id=item.id,
                    annotator_id=annotator.id,
                    label=label,
                    confidence=conf,
                    duration_ms=dur,
                    metadata={"source": "seed_demo"},
                    created_at=base_time + timedelta(hours=offset_h),
                )
                db.add(ann)
                added_annotations += 1

        db.commit()
        print(f"  * Seeded {added_annotations} new Annotations")

        # 6. Compute or seed Trust Scores for all items
        for ext_id, item in items.items():
            try:
                compute_and_save_item_trust_score(
                    db=db,
                    project_id=1,
                    item_id=item.id,
                )
            except Exception as e:
                # Fallback manual trust score if calculation dependencies fail
                existing_ts = db.query(TrustScore).filter(TrustScore.item_id == item.id).first()
                if not existing_ts:
                    score_val = 0.55 if ext_id in ("item-003", "item-007") else 0.92
                    flag = score_val < 0.70
                    ts = TrustScore(
                        project_id=1,
                        item_id=item.id,
                        final_score=score_val,
                        flagged=flag,
                        breakdown={"agreement": score_val, "confidence": score_val},
                    )
                    db.add(ts)
                    db.commit()

        print("  * Computed and saved Trust Scores")

        # Ensure review queue demo flagged items (item-003 and item-007) are flagged for arbitration
        for ext_id in ("item-003", "item-007"):
            if ext_id in items:
                it = items[ext_id]
                ts = db.query(TrustScore).filter(TrustScore.item_id == it.id).first()
                if ts:
                    ts.flagged = True
                    bd = dict(ts.breakdown or {})
                    bd["flag_reason"] = (
                        "Annotator disagreement requires arbitration"
                        if ext_id == "item-007"
                        else "Gold standard verification mismatch"
                    )
                    ts.breakdown = bd
        db.commit()

        # 7. Seed one pending reroute history item for Automation Dashboard
        pending_reroute = (
            db.query(RerouteHistory)
            .filter(RerouteHistory.project_id == 1, RerouteHistory.reroute_status == "PENDING")
            .first()
        )
        if not pending_reroute and "item-007" in items:
            item_7 = items["item-007"]
            reroute = RerouteHistory(
                project_id=1,
                item_id=item_7.id,
                original_annotator_id=annotators["Venkatesh"].id,
                reassigned_annotator_id=None,
                reason="Low confidence and outlier disagreement on item-007",
                trust_score_snapshot=0.58,
                reroute_status="PENDING",
            )
            db.add(reroute)
            db.commit()
            print("  * Seeded pending task reroute for Automation Dashboard")

        # 8. Seed sample external database connectors
        from app.models.external_db_connector import ExternalDBConnector
        connector_count = db.query(ExternalDBConnector).count()
        if connector_count == 0:
            now = datetime.now(timezone.utc)
            conn1 = ExternalDBConnector(
                connection_name="Local Dev Warehouse (SQLite)",
                database_type="sqlite",
                host=None,
                port=None,
                database_name="aqg_dev.db",
                username=None,
                password_encrypted=None,
                status="active",
                read_only=True,
                query_config={"table_name": "annotations"},
                synced_rows_count=40,
                last_tested_at=now,
                last_sync_at=now,
            )
            conn2 = ExternalDBConnector(
                connection_name="Primary Staging Warehouse (PostgreSQL)",
                database_type="postgresql",
                host="localhost",
                port=5432,
                database_name="aqg_db",
                username="postgres",
                password_encrypted="postgres",
                status="active",
                read_only=True,
                query_config={"table_name": "external_annotations"},
                synced_rows_count=1250,
                last_tested_at=now,
                last_sync_at=now,
            )
            db.add(conn1)
            db.add(conn2)
            db.commit()
            print("  * Seeded sample Database Connectors")

        # 9. Seed demo users for auth
        seed_demo_users(db)
        print("  * Seeded Demo Users with RBAC roles")

        # 10. Seed sample A/B Testing Experiment
        from app.models.ab_test_experiment import ABTestExperiment
        exp_count = db.query(ABTestExperiment).filter(ABTestExperiment.project_id == project.id).count()
        if exp_count == 0:
            exp = ABTestExperiment(
                project_id=project.id,
                experiment_name="Guideline Clarification Trial: Ambiguity & Edge Cases",
                schema_version_a={
                    "description": "Baseline instructions: classify sentiment without explicit boundary edge-case definitions.",
                    "labels": ["positive", "negative", "neutral"],
                },
                schema_version_b={
                    "description": "Revised guidelines with boundary contrast examples and few-shot disambiguation.",
                    "labels": ["positive", "negative", "neutral"],
                },
                annotator_group={"allocation": "SPLIT_50_50"},
                assigned_version="SPLIT_50_50",
                status="active",
            )
            db.add(exp)
            db.commit()
            db.refresh(exp)

            # Assign Variant B to Annotators 1 & 2 (higher gold agreement) and Variant A to 3 & 4
            for ann in db.query(Annotation).filter(Annotation.project_id == project.id).all():
                meta = dict(ann.metadata_ or {})
                if ann.annotator_id in (1, 2):
                    meta["schema_version"] = "B"
                    meta["variant"] = "B"
                else:
                    meta["schema_version"] = "A"
                    meta["variant"] = "A"
                ann.metadata_ = meta
            db.commit()
            print("  * Seeded sample A/B Testing Experiment with variant comparison metrics")

        print("[OK] Demo data seeding completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
