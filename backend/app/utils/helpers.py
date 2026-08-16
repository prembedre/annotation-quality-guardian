"""
General-purpose helper functions.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def load_csv(filepath: str | Path) -> List[Dict[str, Any]]:
    """Load a CSV file and return a list of row dictionaries."""
    filepath = Path(filepath)
    with filepath.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_json(filepath: str | Path) -> Any:
    """Load a JSON file and return the parsed content."""
    filepath = Path(filepath)
    with filepath.open(encoding="utf-8") as f:
        return json.load(f)
