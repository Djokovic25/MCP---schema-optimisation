import json
from pathlib import Path
from typing import List, Dict, Any


def load_tasks(path: str) -> List[Dict[str, Any]]:
    """Load experiment tasks from a JSON file."""

    task_path = Path(path)

    with task_path.open("r", encoding="utf-8") as f:
        return json.load(f)