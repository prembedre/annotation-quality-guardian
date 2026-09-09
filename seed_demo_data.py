"""
Root convenience script to seed AQG Demo Data.
"""

import sys
import os

# Add root and backend to python path
root_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(root_dir, "backend")

sys.path.insert(0, root_dir)
sys.path.insert(0, backend_dir)

# Default to the SQLite database if DATABASE_URL is not set
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(root_dir, 'aqg_dev.db')}"

from backend.app.core.seed_demo_data import seed_demo_data

if __name__ == "__main__":
    seed_demo_data()
