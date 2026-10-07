# Experiment Log

## Experiment 1 — Full-Schema Baseline

### Purpose

Establish the performance of Gemini when the complete tool schema is
available before performing schema-component ablations.

### Research question

How accurately does the model construct tool invocations when provided
with the complete schema?

### Model

Gemini 3.1 Flash-Lite

### Tool

search_issues

### Schema

schemas/synthetic/search_issues_v2.json

### Task set

tasks/schema_ablation_tasks_v2.json

15 tasks:
- 5 easy
- 5 medium
- 5 hard

### Function-calling setup

Native Gemini function calling was used.

The model received the tool declaration through the API rather than
being prompted to produce simulated JSON.

Automatic function execution was disabled.

Tool selection was constrained to the target function so that the
experiment focused on argument construction rather than tool selection.

### Schema disclosure

Full schema was disclosed.

No schema components were removed.

### Evaluation

The model-generated function name and arguments were compared against
the expected invocation.

Evaluation metrics:
- tool correctness
- schema validity
- argument correctness
- task success
- failure type
- input tokens
- output tokens
- latency

The complete/original schema was used for evaluation even when the
disclosed schema is later ablated.

### Baseline result

15 task evaluations were performed.

Task success:
14/15 = 93.3%

### Observed failure

H4 failed.

Task:
"Find closed AUTH_FAILURES issues, show the newest issues first,
include comments, and return 50 results."

Expected:
- q = AUTH_FAILURES
- state = closed
- sort = created_desc
- with_comments = true
- limit = 50

Model output used:
- limit = 5

All other required arguments were correctly constructed.

Failure type:
arguments_incorrect

### Benchmark correction

H5 initially contained wording that allowed a semantic reinterpretation
of AUTH_FAILURES. The task was revised so that the intended query term
was unambiguous without requiring quotation marks.

The corrected H5 task was rerun and succeeded.

This correction was made to remove an ambiguity in the benchmark rather
than to improve model performance.

### Status

The full-schema baseline is frozen and is used as the reference
condition for subsequent schema-component ablation experiments.

Raw results:
results/schema_ablation_v2_baseline/baseline_raw_results.jsonl