"""
AQG Database Migration Tool: SQLite to PostgreSQL
Safely transfers records from local SQLite (e.g. aqg_dev.db) into hosted PostgreSQL (Neon, Supabase, RDS).

Features:
- Preserves primary keys, foreign keys, timestamps, and metadata.
- Idempotent: checks existing IDs to avoid duplicates.
- Resets PostgreSQL identity/serial sequences to prevent future ID collisions.
- Validates migrated row counts table-by-table.
- Sanitizes output to avoid exposing credentials or password hashes.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aqg_migration")

# Topological migration order to respect foreign key constraints
TABLE_ORDER = [
    "users",
    "projects",
    "annotators",
    "items",
    "annotations",
    "trust_scores",
    "behavioral_scores",
    "embedding_results",
    "project_thresholds",
    "reviewer_decisions",
    "external_db_connectors",
    "reroute_histories",
    "ab_test_experiments",
    "automation_rules",
]

# Columns stored as JSON in SQLite that need parsing/handling
JSON_COLUMNS = {
    "projects": {"label_set"},
    "items": {"content"},
    "annotations": {"metadata"},
    "trust_scores": {"breakdown"},
    "behavioral_scores": {"details"},
    "embedding_results": {"embedding", "details"},
    "external_db_connectors": {"query_config"},
    "ab_test_experiments": {"schema_version_a", "schema_version_b", "annotator_group"},
}

# Boolean columns stored as 0/1 in SQLite
BOOLEAN_COLUMNS = {
    "users": {"is_active"},
    "projects": {"automation_enabled", "is_archived"},
    "items": {"is_gold"},
    "trust_scores": {"flagged"},
    "embedding_results": {"is_outlier"},
    "external_db_connectors": {"read_only"},
    "automation_rules": {"active"},
}


def clean_url(url: str) -> str:
    """Normalize postgres:// to postgresql://."""
    url = (url or "").strip()
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def mask_url(url: str) -> str:
    """Mask database password in connection string for logging."""
    try:
        from sqlalchemy.engine.url import make_url
        u = make_url(url)
        return u.render_as_string(hide_password=True)
    except Exception:
        return "masked_url"


def migrate_data(sqlite_path: str, postgres_url: str, dry_run: bool = False) -> bool:
    """
    Main migration routine.
    """
    if not os.path.isabs(sqlite_path) and not os.path.exists(sqlite_path):
        # Look in repository root or backend
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        root_dir = os.path.dirname(base_dir)
        for cand in [
            os.path.join(root_dir, sqlite_path),
            os.path.join(base_dir, sqlite_path),
        ]:
            if os.path.exists(cand):
                sqlite_path = cand
                break

    if not os.path.exists(sqlite_path):
        logger.error("Source SQLite database not found at: %s", sqlite_path)
        return False

    postgres_url = clean_url(postgres_url)
    if not postgres_url or not postgres_url.startswith("postgresql"):
        logger.error(
            "Target PostgreSQL URL must begin with 'postgresql://' or 'postgres://'. Got: %s",
            mask_url(postgres_url),
        )
        return False

    logger.info("Source SQLite:     %s (%d bytes)", sqlite_path, os.path.getsize(sqlite_path))
    logger.info("Target PostgreSQL: %s", mask_url(postgres_url))

    src_engine = create_engine(f"sqlite:///{sqlite_path.replace('\\', '/')}", connect_args={"check_same_thread": False})
    tgt_engine = create_engine(postgres_url, pool_pre_ping=True)

    # 1. Test connectivity
    try:
        with tgt_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully connected to target PostgreSQL database.")
    except Exception as exc:
        logger.error("Failed to connect to target PostgreSQL database: %s", exc)
        return False

    # 2. Ensure schema exists on target PostgreSQL
    try:
        # Import Base and models to ensure all tables are registered
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.models import Base
        Base.metadata.create_all(bind=tgt_engine)
        from app.core.db_patch import ensure_schema_compatibility
        ensure_schema_compatibility(tgt_engine)
        logger.info("Verified target PostgreSQL schema and compatibility.")
    except Exception as exc:
        logger.error("Schema creation failed on target: %s", exc)
        return False

    src_inspector = inspect(src_engine)
    tgt_inspector = inspect(tgt_engine)

    src_tables = set(src_inspector.get_table_names())
    tgt_tables = set(tgt_inspector.get_table_names())

    validation_summary = {}

    for table in TABLE_ORDER:
        if table not in src_tables:
            logger.info("Skipping '%s': table not found in source SQLite.", table)
            continue
        if table not in tgt_tables:
            logger.warning("Target table '%s' missing in PostgreSQL. Skipping.", table)
            continue

        src_cols = [c["name"] for c in src_inspector.get_columns(table)]
        tgt_cols = {c["name"] for c in tgt_inspector.get_columns(table)}

        # Intersect columns
        common_cols = [c for c in src_cols if c in tgt_cols]
        if not common_cols:
            continue

        with src_engine.connect() as s_conn:
            col_list_str = ", ".join(f'"{c}"' for c in common_cols)
            src_rows = s_conn.execute(text(f'SELECT {col_list_str} FROM "{table}"')).fetchall()

        src_count = len(src_rows)
        if src_count == 0:
            logger.info("Table '%s': 0 rows in source SQLite.", table)
            validation_summary[table] = {"source": 0, "target_before": 0, "migrated": 0, "status": "EMPTY"}
            continue

        json_cols = JSON_COLUMNS.get(table, set())
        bool_cols = BOOLEAN_COLUMNS.get(table, set())

        with tgt_engine.begin() as t_conn:
            existing_ids = set()
            if "id" in tgt_cols:
                res = t_conn.execute(text(f'SELECT "id" FROM "{table}"')).fetchall()
                existing_ids = {r[0] for r in res}

            inserted_count = 0
            updated_count = 0

            for row in src_rows:
                row_dict = dict(zip(common_cols, row))
                row_id = row_dict.get("id")

                # Format JSON and Boolean values
                for col, val in row_dict.items():
                    if col in json_cols and isinstance(val, str):
                        try:
                            row_dict[col] = json.loads(val)
                        except Exception:
                            pass
                    elif col in bool_cols and val is not None:
                        row_dict[col] = bool(val)

                if dry_run:
                    inserted_count += 1
                    continue

                if row_id is not None and row_id in existing_ids:
                    # Update existing record
                    set_clauses = [f'"{c}" = :{c}' for c in common_cols if c != "id"]
                    if set_clauses:
                        stmt = text(f'UPDATE "{table}" SET {", ".join(set_clauses)} WHERE "id" = :id')
                        t_conn.execute(stmt, row_dict)
                    updated_count += 1
                else:
                    # Insert new record
                    cols_str = ", ".join(f'"{c}"' for c in common_cols)
                    vals_str = ", ".join(f':{c}' for c in common_cols)
                    stmt = text(f'INSERT INTO "{table}" ({cols_str}) VALUES ({vals_str})')
                    t_conn.execute(stmt, row_dict)
                    inserted_count += 1

            # 3. Reset PostgreSQL sequence for auto-increment IDs
            if not dry_run and "id" in tgt_cols:
                try:
                    t_conn.execute(
                        text(
                            f"SELECT setval(pg_get_serial_sequence('\"{table}\"', 'id'), "
                            f"COALESCE((SELECT MAX(id) FROM \"{table}\"), 1), "
                            f"(SELECT MAX(id) FROM \"{table}\") IS NOT NULL);"
                        )
                    )
                except Exception as seq_exc:
                    logger.debug("Sequence reset notice for %s: %s", table, seq_exc)

        # Validate target count
        with tgt_engine.connect() as t_conn:
            final_tgt_count = t_conn.execute(text(f'SELECT count(*) FROM "{table}"')).scalar()

        status_str = "DRY-RUN" if dry_run else ("OK" if final_tgt_count >= src_count else "MISMATCH")
        logger.info(
            "Table '%s': %d in source -> %d in target (+%d new, %d updated) [%s]",
            table,
            src_count,
            final_tgt_count,
            inserted_count,
            updated_count,
            status_str,
        )
        validation_summary[table] = {
            "source": src_count,
            "target_final": final_tgt_count,
            "new_inserted": inserted_count,
            "updated": updated_count,
            "status": status_str,
        }

    logger.info("================== MIGRATION SUMMARY ==================")
    all_ok = True
    for tbl, res in validation_summary.items():
        logger.info("  %-25s : Source=%-4d Target=%-4d [%s]", tbl, res["source"], res.get("target_final", 0), res["status"])
        if res["status"] not in ("OK", "EMPTY", "DRY-RUN"):
            all_ok = False
    logger.info("=======================================================")

    return all_ok


def main():
    parser = argparse.ArgumentParser(description="Migrate local AQG SQLite data to hosted PostgreSQL.")
    parser.add_argument(
        "--sqlite-path",
        default="aqg_dev.db",
        help="Path to source SQLite database file (default: aqg_dev.db)",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.environ.get("TARGET_DATABASE_URL") or os.environ.get("DATABASE_URL"),
        help="Target PostgreSQL connection URI (defaults to DATABASE_URL env var)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect source and target without writing any rows",
    )

    args = parser.parse_args()

    if not args.postgres_url:
        logger.error(
            "No PostgreSQL target URL specified. "
            "Please pass --postgres-url or set DATABASE_URL or TARGET_DATABASE_URL environment variable."
        )
        sys.exit(1)

    success = migrate_data(args.sqlite_path, args.postgres_url, dry_run=args.dry_run)
    if not success:
        logger.error("Migration finished with errors. Review log above.")
        sys.exit(1)
    logger.info("Migration completed successfully!")


if __name__ == "__main__":
    main()
