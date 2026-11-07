"""
Vercel Serverless Function entrypoint.
Enables standard zero-config Vercel Python runtime routing for /api and /auth.
"""

import os
import sys

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_curr_dir)
_backend_dir = os.path.join(_root_dir, "backend")
_scoring_dir = os.path.join(_root_dir, "scoring")

for d in [_root_dir, _backend_dir, _scoring_dir]:
    if d not in sys.path:
        sys.path.insert(0, d)

from backend.main import app

__all__ = ["app"]
