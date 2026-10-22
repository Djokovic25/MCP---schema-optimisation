
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "results/combined_qwen_results.json"
OUT = ROOT / "results/paper_tables_qwen"

OUT.mkdir(parents=True, exist_ok=True)

with open(INPUT, encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

required = [
    "task_set", "condition", "task_success",
    "schema_valid", "arguments_correct",
    "input_tokens", "output_tokens", "latency_ms"
]
missing = [col for col in required if col not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# Convert metrics to numeric where applicable.
for col in [
    "task_success", "schema_valid", "arguments_correct",
    "input_tokens", "output_tokens", "latency_ms"
]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Explicit condition order for paper tables.
condition_order = [
    "full",
    "relevant_only",
    "relevant_plus_one_irrelevant",
    "minimal_relevant"
]

def summarize(group):
    n = len(group)
    result = {
        "trials": n,
        "successful_trials": group["task_success"].sum(),
        "task_success_%": 100 * group["task_success"].mean(),
        "schema_valid_%": 100 * group["schema_valid"].mean(),
        "arguments_correct_%": 100 * group["arguments_correct"].mean(),
        "mean_input_tokens": group["input_tokens"].mean(),
        "mean_output_tokens": group["output_tokens"].mean(),
        "mean_latency_ms": group["latency_ms"].mean(),
        "median_latency_ms": group["latency_ms"].median(),
        "latency_sd_ms": group["latency_ms"].std(),
    }

    if "tool_correct" in group.columns:
        result["tool_correct_%"] = (
            100 * pd.to_numeric(
                group["tool_correct"], errors="coerce"
            ).mean()
        )

    return pd.Series(result)

# Table A: pooled descriptive summary by condition.
pooled = (
    df.groupby("condition", dropna=False)
      .apply(summarize, include_groups=False)
      .reindex(condition_order)
      .reset_index()
)

# Table B: results split by original vs new task set.
by_task_set = (
    df.groupby(["task_set", "condition"], dropna=False)
      .apply(summarize, include_groups=False)
      .reset_index()
)

# Round for presentation.
numeric_cols = pooled.select_dtypes(include="number").columns
pooled[numeric_cols] = pooled[numeric_cols].round(2)

numeric_cols = by_task_set.select_dtypes(include="number").columns
by_task_set[numeric_cols] = by_task_set[numeric_cols].round(2)

pooled.to_csv(OUT / "qwen_main_results.csv", index=False)
by_task_set.to_csv(OUT / "qwen_results_by_task_set.csv", index=False)

# LaTeX versions for a paper draft.
pooled.to_latex(
    OUT / "qwen_main_results.tex",
    index=False,
    escape=True,
    na_rep="—"
)
by_task_set.to_latex(
    OUT / "qwen_results_by_task_set.tex",
    index=False,
    escape=True,
    na_rep="—"
)

print("Input records:", len(df))
print("\nRecords by task set:")
print(df["task_set"].value_counts().to_string())

print("\nMain results table:")
print(pooled.to_string(index=False))

print("\nResults by task set:")
print(by_task_set.to_string(index=False))

print(f"\nTables saved in: {OUT}")
