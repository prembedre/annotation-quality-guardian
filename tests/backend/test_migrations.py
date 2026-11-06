"""
Tests for Alembic migrations running on clean SQLite.
"""

import os
import tempfile
from pathlib import Path
from alembic import command
from alembic.config import Config
import sqlalchemy as sa


def test_alembic_clean_sqlite_migrations():
    """
    Run alembic upgrade head followed by alembic downgrade base
    on an isolated temporary SQLite database to verify all migrations execute cleanly.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        backend_dir = Path(__file__).resolve().parents[2] / "backend"
        ini_path = str(backend_dir / "alembic.ini")
        migrations_dir = str(backend_dir / "migrations")
        db_url = f"sqlite:///{tmp_db_path}"

        # Override DATABASE_URL
        old_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = db_url

        try:
            cfg = Config(ini_path)
            cfg.set_main_option("script_location", migrations_dir)
            cfg.set_main_option("sqlalchemy.url", db_url)

            # Upgrade to head
            command.upgrade(cfg, "head")

            # Inspect created tables
            engine = sa.create_engine(db_url)
            inspector = sa.inspect(engine)
            tables = inspector.get_table_names()

            expected_tables = {
                "items",
                "annotations",
                "annotators",
                "projects",
                "trust_scores",
                "behavioral_scores",
                "embedding_results",
                "project_thresholds",
                "reviewer_decisions",
                "external_db_connectors",
                "reroute_histories",
                "ab_test_experiments",
                "users",
                "automation_rules",
            }
            for table in expected_tables:
                assert table in tables, f"Expected table '{table}' not found in upgraded SQLite schema: {tables}"

            # Downgrade to base
            command.downgrade(cfg, "base")

            # Verify tables were dropped (0002 deliberately preserves 'projects' table to protect project data)
            inspector_after = sa.inspect(engine)
            tables_after = [t for t in inspector_after.get_table_names() if t != "alembic_version"]
            assert set(tables_after).issubset({"projects"}), f"Expected only preserved tables after downgrade, but found: {tables_after}"
        finally:
            if old_url is not None:
                os.environ["DATABASE_URL"] = old_url
            else:
                os.environ.pop("DATABASE_URL", None)
    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except OSError:
                pass
