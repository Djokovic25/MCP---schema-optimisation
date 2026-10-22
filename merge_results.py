
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent

FILES = [
    (
        "original_36_tasks",
        ROOT / "results/schema_disclosure_synthetic_groq_qwen/raw_results.json",
    ),
    (
        "new_108_tasks",
        ROOT / "results/schema_disclosure_v2_groq_qwen/raw_results.json",
    ),
]

OUTPUT = ROOT / "results/combined_qwen_results.json"

combined = []

for source, path in FILES:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError(f"Expected a list of records in {path}")

    print(f"{source}: {len(records)} records")

    for record in records:
        row = dict(record)
        row["task_set"] = source
        combined.append(row)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2, ensure_ascii=False)

print(f"\nTotal Qwen records: {len(combined)}")
print(f"Saved to: {OUTPUT}")

print("\nCounts by task set:")
for task_set, count in Counter(r["task_set"] for r in combined).items():
    print(f"{task_set}: {count}")

print("\nCounts by task set and condition:")
counts = Counter(
    (r["task_set"], r.get("condition")) for r in combined
)
for key, count in sorted(counts.items()):
    print(f"{key[0]} | {key[1]}: {count}")
