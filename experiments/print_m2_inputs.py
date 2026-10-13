import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.schemas.disclosure import build_task_disclosure

SCHEMA_PATH = ROOT / "schemas/synthetic/search_issues_v2.json"
TASKS_PATH = ROOT / "tasks/schema_disclosure_tasks_v1.json"

with open(SCHEMA_PATH, encoding="utf-8") as f:
    full_schema = json.load(f)

with open(TASKS_PATH, encoding="utf-8") as f:
    tasks_data = json.load(f)

# Support either a JSON list or an object containing a task list.
if isinstance(tasks_data, list):
    tasks = tasks_data
else:
    tasks = tasks_data.get("tasks", [])

task = next(t for t in tasks if t["id"] == "M2")

print("=" * 80)
print("EXACT M2 TASK RECORD")
print("=" * 80)
print(json.dumps(task, indent=2, ensure_ascii=False))

for condition in ("relevant_only", "minimal_relevant"):
    disclosed_schema = build_task_disclosure(
        schema=full_schema,
        relevant_parameters=task["relevant_parameters"],
        condition=condition,
    )

    print("\n" + "=" * 80)
    print(f"SCHEMA: {condition}")
    print("=" * 80)
    print(json.dumps(disclosed_schema, indent=2, ensure_ascii=False))