#!/usr/bin/env python
"""
AQG Database Migration CLI Tool.
Delegates to app.core.migration.migrate_data
"""
import os
import sys
import argparse
import logging

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.dirname(_curr_dir)
_root_dir = os.path.dirname(_backend_dir)

for d in [_root_dir, _backend_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

from app.core.migration import migrate_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("aqg_migration")


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
