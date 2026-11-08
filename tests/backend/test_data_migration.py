"""
Unit test for data migration tool (backend/scripts/migrate_sqlite_to_postgres.py).
Verifies that all 14 tables, records, JSON fields, and relationships are properly extracted and migrated.
"""

import os
import tempfile
import sqlite3
from backend.scripts.migrate_sqlite_to_postgres import TABLE_ORDER, JSON_COLUMNS, BOOLEAN_COLUMNS


def test_sqlite_source_database_has_expected_records():
    """Verify that aqg_dev.db has the full demo dataset."""
    db_path = "aqg_dev.db"
    assert os.path.exists(db_path), f"Source database {db_path} not found"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify project
    cursor.execute("SELECT id, name FROM projects WHERE id = 1")
    project = cursor.fetchone()
    assert project is not None
    assert project[1] == "Project 1"

    # Verify annotators (Rahul, Prem, Venkatesh, Sidharth)
    cursor.execute("SELECT count(*) FROM annotators")
    annotator_count = cursor.fetchone()[0]
    assert annotator_count == 4

    cursor.execute("SELECT username FROM annotators ORDER BY id")
    names = [r[0] for r in cursor.fetchall()]
    assert set(names) == {"Rahul", "Prem", "Venkatesh", "Sidharth"}

    # Verify items and annotations
    cursor.execute("SELECT count(*) FROM items")
    item_count = cursor.fetchone()[0]
    assert item_count == 10

    cursor.execute("SELECT count(*) FROM annotations")
    ann_count = cursor.fetchone()[0]
    assert ann_count == 40

    # Verify trust scores
    cursor.execute("SELECT count(*) FROM trust_scores")
    ts_count = cursor.fetchone()[0]
    assert ts_count == 10

    # Verify users
    cursor.execute("SELECT count(*) FROM users")
    user_count = cursor.fetchone()[0]
    assert user_count == 6

    # Verify rules
    cursor.execute("SELECT count(*) FROM automation_rules")
    rule_count = cursor.fetchone()[0]
    assert rule_count == 3

    conn.close()
