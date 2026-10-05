import json
from pathlib import Path
from typing import Dict, Any


def load_schema(path: str) -> Dict[str, Any]:
    """Load a tool schema from a JSON file."""

    schema_path = Path(path)

    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)