"""
Vercel FastAPI entrypoint module.
Exposes the core FastAPI instance 'app' for ASGI runners and Vercel Services.
"""

import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
if _curr_dir not in sys.path:
    sys.path.insert(0, _curr_dir)

_scoring_dir = os.path.join(_curr_dir, "scoring")
if os.path.exists(_scoring_dir) and _scoring_dir not in sys.path:
    sys.path.insert(0, _scoring_dir)

from app.main import app

__all__ = ["app"]

