#!/usr/bin/env python
"""
AQG Data Migration Entry Point.
Delegates to backend/scripts/migrate_sqlite_to_postgres.py
"""
import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_curr_dir) if os.path.basename(_curr_dir) == "scripts" else _curr_dir
_backend_dir = os.path.join(_root_dir, "backend")

for d in [_root_dir, _backend_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

from backend.scripts.migrate_sqlite_to_postgres import main

if __name__ == "__main__":
    main()
