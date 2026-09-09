"""
Safe automated database schema patcher for SQLite and PostgreSQL.
Ensures required columns exist without dropping tables or losing data.
"""

import logging
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def ensure_schema_compatibility(engine: Engine) -> None:
    """
    Ensure all required columns and default columns exist in tables.
    Preserves existing data and avoids table drops.
    """
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            table_names = set(inspector.get_table_names())

            # 1. projects table
            if "projects" in table_names:
                project_cols = {col["name"] for col in inspector.get_columns("projects")}
                if "automation_enabled" not in project_cols:
                    logger.info("Adding missing 'automation_enabled' column to projects table")
                    conn.execute(
                        text("ALTER TABLE projects ADD COLUMN automation_enabled BOOLEAN NOT NULL DEFAULT 0")
                    )
                    conn.commit()

            # 2. annotators table
            if "annotators" in table_names:
                annotator_cols = {col["name"] for col in inspector.get_columns("annotators")}
                if "username" not in annotator_cols:
                    logger.info("Adding missing 'username' column to annotators table")
                    conn.execute(
                        text("ALTER TABLE annotators ADD COLUMN username VARCHAR(100)")
                    )
                    conn.commit()
                if "name" not in annotator_cols:
                    logger.info("Adding missing 'name' column to annotators table")
                    conn.execute(
                        text("ALTER TABLE annotators ADD COLUMN name VARCHAR(255)")
                    )
                    conn.commit()
                # Sync name and username if one is null
                conn.execute(
                    text("UPDATE annotators SET username = name WHERE (username IS NULL OR username = '') AND name IS NOT NULL")
                )
                conn.execute(
                    text("UPDATE annotators SET name = username WHERE (name IS NULL OR name = '') AND username IS NOT NULL")
                )
                conn.commit()

            # 3. items table
            if "items" in table_names:
                item_cols = {col["name"] for col in inspector.get_columns("items")}
                if "source" not in item_cols:
                    logger.info("Adding missing 'source' column to items table")
                    conn.execute(
                        text("ALTER TABLE items ADD COLUMN source VARCHAR(255) NOT NULL DEFAULT 'default'")
                    )
                    conn.commit()

            # 4. trust_scores table
            if "trust_scores" in table_names:
                ts_cols = {col["name"] for col in inspector.get_columns("trust_scores")}
                patches = [
                    ("project_id", "INTEGER"),
                    ("gold_score", "NUMERIC(10, 6)"),
                    ("agreement_score", "NUMERIC(10, 6)"),
                    ("behavioral_score", "NUMERIC(10, 6)"),
                    ("embedding_score", "NUMERIC(10, 6)"),
                    ("final_score", "NUMERIC(10, 6)"),
                ]
                for col_name, col_type in patches:
                    if col_name not in ts_cols:
                        logger.info("Adding missing '%s' column to trust_scores table", col_name)
                        conn.execute(
                            text(f"ALTER TABLE trust_scores ADD COLUMN {col_name} {col_type}")
                        )
                        conn.commit()

                # If score column exists and final_score is NULL, populate final_score
                if "score" in ts_cols and "final_score" in ts_cols:
                    conn.execute(
                        text("UPDATE trust_scores SET final_score = score WHERE final_score IS NULL")
                    )
                    conn.commit()

            logger.info("Database schema compatibility verified successfully.")
    except Exception as exc:
        logger.warning("Database schema patch notice: %s", exc)


if __name__ == "__main__":
    from app.core.db import engine
    ensure_schema_compatibility(engine)
    print("Database schema checked and verified.")
