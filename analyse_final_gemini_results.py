
import json
from pathlib import Path
import pandas as pd

path = Path(
    "results/schema_disclosure_synthetic_gemini/raw_results.json"
)
out = Path("results/schema_disclosure_synthetic_gemini/analysis")
out.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(json.loads(path.read_text(encoding="utf-8")))

# Failure-type counts and percentages by condition
failures = df[df["task_success"] == False].copy()

failure_summary = (
    failures.groupby(["condition", "failure_type"], dropna=False)
    .size()
    .rename("count")
    .reset_index()
)

failure_summary["pct_of_condition_trials"] = failure_summary.apply(
    lambda r: 100 * r["count"] / (df["condition"] == r["condition"]).sum(),
    axis=1,
).round(2)

print("\nFAILURE TYPES")
print(failure_summary.to_string(index=False))
failure_summary.to_csv(out / "failure_type_summary.csv", index=False)

# Tool selection versus argument correctness
tool_summary = (
    df.groupby("condition")
    .agg(
        trials=("task_success", "size"),
        correct_tool_rate=("tool_correct", "mean"),
        schema_valid_rate=("schema_valid", "mean"),
        correct_arguments_rate=("arguments_correct", "mean"),
        task_success_rate=("task_success", "mean"),
    )
    .reset_index()
)

for col in [
    "correct_tool_rate",
    "schema_valid_rate",
    "correct_arguments_rate",
    "task_success_rate",
]:
    tool_summary[col] = (100 * tool_summary[col]).round(2)

print("\nTOOL AND ARGUMENT METRICS")
print(tool_summary.to_string(index=False))
tool_summary.to_csv(out / "tool_argument_summary.csv", index=False)

# Task-level success consistency across repetitions
per_task = (
    df.groupby(["task_id", "condition"])
    .agg(
        repetitions=("task_success", "size"),
        successes=("task_success", "sum"),
        success_rate=("task_success", "mean"),
    )
    .reset_index()
)

per_task["success_rate"] = (100 * per_task["success_rate"]).round(2)

consistency = (
    per_task.groupby(["condition", "successes"])
    .size()
    .rename("number_of_tasks")
    .reset_index()
)

print("\nTASK CONSISTENCY ACROSS 3 REPETITIONS")
print(consistency.to_string(index=False))
consistency.to_csv(out / "task_consistency.csv", index=False)

print("\nSaved analysis tables to:", out.resolve())
