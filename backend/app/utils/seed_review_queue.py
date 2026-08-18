"""
Create sample flagged records for Review Queue testing.
"""

from app.core.db import SessionLocal
from app.models.item import Item
from app.models.trust_score import TrustScore


def seed_flagged_items():
    db = SessionLocal()

    try:
        items = [
            Item(
                source="review_queue_test",
                content={
                    "text": "Sample flagged item 1"
                },
            ),
            Item(
                source="review_queue_test",
                content={
                    "text": "Sample flagged item 2"
                },
            ),
            Item(
                source="review_queue_test",
                content={
                    "text": "Sample normal item"
                },
            ),
        ]

        db.add_all(items)
        db.flush()

        scores = [
            TrustScore(
                item_id=items[0].id,
                score=0.32,
                breakdown={
                    "gold_accuracy": 0.40,
                    "agreement": 0.30,
                    "anomaly": 0.25,
                    "embedding": 0.35,
                },
                flagged=True,
            ),
            TrustScore(
                item_id=items[1].id,
                score=0.41,
                breakdown={
                    "gold_accuracy": 0.50,
                    "agreement": 0.35,
                    "anomaly": 0.30,
                    "embedding": 0.45,
                },
                flagged=True,
            ),
            TrustScore(
                item_id=items[2].id,
                score=0.91,
                breakdown={
                    "gold_accuracy": 0.95,
                    "agreement": 0.90,
                    "anomaly": 0.92,
                    "embedding": 0.88,
                },
                flagged=False,
            ),
        ]

        db.add_all(scores)
        db.commit()

        print("Sample Review Queue records created successfully.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_flagged_items()
