#!/usr/bin/env bash
set -e

# ==============================================================================
# Annotation Quality Guardian — Backend Container Entrypoint
# ==============================================================================

echo "==> [AQG Entrypoint] Starting container initialization..."

# Wait for PostgreSQL database if configured with a remote host
python - << 'EOF'
import os
import sys
import time
import socket
from urllib.parse import urlparse

db_url = os.environ.get("DATABASE_URL", "")
if "postgres" in db_url:
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname or "db"
        port = parsed.port or 5432
        print(f"==> [AQG Entrypoint] Checking database connectivity ({host}:{port})...")
        deadline = time.time() + 45
        connected = False
        while time.time() < deadline:
            try:
                s = socket.create_connection((host, port), timeout=2)
                s.close()
                connected = True
                print(f"==> [AQG Entrypoint] Database is ready at {host}:{port}!")
                break
            except OSError:
                time.sleep(1)
        if not connected:
            print(f"==> [AQG Entrypoint] Warning: Timed out connecting to database at {host}:{port}. Proceeding anyway...")
    except Exception as exc:
        print(f"==> [AQG Entrypoint] Warning: Could not parse DATABASE_URL: {exc}")
else:
    print("==> [AQG Entrypoint] Using local/SQLite database. Skipping network check.")
EOF

# Run database migrations with Alembic
echo "==> [AQG Entrypoint] Running database migrations..."
if alembic upgrade head; then
    echo "==> [AQG Entrypoint] Database migrations applied successfully."
else
    echo "==> [AQG Entrypoint] Warning: Migration failed or database already up-to-date. Continuing..."
fi

# Optional seed demo data on fresh setup if SEED_DEMO_DATA=true
if [ "${SEED_DEMO_DATA}" = "true" ] || [ "${SEED_DEMO_DATA}" = "1" ]; then
    echo "==> [AQG Entrypoint] SEED_DEMO_DATA requested. Seeding initial records..."
    python -m app.core.seed_demo_data || python seed_demo_data.py || true
fi

echo "==> [AQG Entrypoint] Initialization complete. Executing application command: $@"
exec "$@"
