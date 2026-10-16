# Groq Schema-Disclosure Experiment

## Overview

This experiment studies how the amount and type of tool-schema
information provided to a language model affects tool-call argument
correctness and token cost.

- **Provider:** Groq API
- **Model:** `openai/gpt-oss-20b`
- **Tool:** `search_issues`
- **Schema:** `schemas/synthetic/search_issues_v2.json`
- **Tasks:** `tasks/schema_disclosure_tasks_v1.json`
- **Tasks per run:** 15 (easy, medium, hard)
- **Repetitions:** 3 per task-condition pair
- **Conditions:** 4
- **Planned/completed trials:** 15 × 4 × 3 = 180
- **Raw results:** `results/schema_disclosure_groq/raw_results.json`
- **Error log:** `results/schema_disclosure_groq/errors.jsonl`
- **Config:** `configs/schema_disclosure_groq.yaml`
- **Runner:** `experiments/run_schema_disclosure_groq.py`

This is an exploratory benchmark. Results describe this task set and
should not be generalized to all tools, tasks, or models.

## Research question

How does disclosing the full tool schema, only task-relevant fields, or
a reduced schema affect tool-call correctness and token cost?

## Disclosure conditions

1.  **`full`** — Full tool schema.
2.  **`relevant_only`** — Only parameters marked relevant to the task
    are exposed, with their schema information retained.
3.  **`relevant_plus_one_irrelevant`** — Relevant parameters plus one
    additional irrelevant parameter.
4.  **`minimal_relevant`** — Reduced relevant-parameter schema, removing
    tool/parameter descriptions and numeric constraints while retaining
    types and enum information.

Check `src/schemas/disclosure.py` for the exact implementation of these
conditions.

## How to run

From the project root:

``` bash
source mcp-env/bin/activate
python experiments/run_schema_disclosure_groq.py
```

The project uses a `.env` file for credentials. It should contain
`GROQ_API_KEY=...`. Never commit `.env` or paste the API key into logs,
notebooks, or messages.

Inspect the config and existing output before rerunning so separate runs
are not accidentally mixed or overwritten.

## Evaluation

Each generated call is evaluated against the full schema and the task’s
expected arguments. The recorded outcomes include tool selection, schema
validity, argument correctness, overall task success, failure type,
token usage, and latency.

**Important caveat:** exact dictionary equality may mark a call
incorrect because it includes extra optional fields or uses a different
but potentially equivalent query representation. Do not automatically
treat these as semantically correct either. Audit expected arguments,
schema defaults, and task intent before changing the evaluator. Preserve
strict exact-match results and report any separately defined
semantic-equivalence metric alongside them.

## Completed results

The raw result file contains 180 records: 45 trials per condition (15
tasks × 3 repetitions).

| Condition                 | Successes | Accuracy | Mean input tokens | Median input tokens | Mean output tokens | Mean latency (ms) |
|:--------------------------|----------:|---------:|-------------------|--------------------:|-------------------:|------------------:|
| Full                      |     10/45 |    22.2% | 334.3             |                 330 |              135.9 |             988.8 |
| Relevant only             |     41/45 |    91.1% | 214.2             |                 200 |              107.3 |             948.0 |
| Relevant + one irrelevant |     14/45 |    31.1% | 237.2             |                 227 |              103.4 |            1041.6 |
| Minimal relevant          |     29/45 |    64.4% | 154.3             |                 152 |              106.7 |             960.2 |

Input-token reduction relative to full:

| Condition                 | Input-token reduction |
|:--------------------------|----------------------:|
| Relevant only             |                 35.9% |
| Relevant + one irrelevant |                 29.1% |
| Minimal relevant          |                 53.9% |

All trials selected the expected tool and produced schema-valid
arguments according to the current evaluator. All failures were
categorized as `arguments_incorrect`.

### Descriptive interpretation

- `relevant_only` had the highest observed accuracy in this run and
  lower input-token usage than `full`.
- `minimal_relevant` used the fewest input tokens, but its observed
  accuracy was lower than `relevant_only`.
- `relevant_plus_one_irrelevant` performed substantially worse than
  `relevant_only`; inspect exactly which field was added and how it
  affected arguments.
- Full-schema accuracy was unexpectedly low for this model. Do not
  assume schema length alone caused the difference.
- There are only 15 distinct tasks. Repeated calls on the same task are
  not 45 independent task examples.
- Latency differences are descriptive; this run does not establish a
  reliable latency advantage.

Recalculate all results from raw data if the result file or evaluator
changes.

## Recommended next steps

1.  Audit failures: missing fields, extra fields, incorrect values,
    query-format mismatches, and possible default-value differences.
2.  Review the evaluator and define which arguments are required,
    optional, defaulted, or semantically equivalent.
3.  Inspect which irrelevant parameter is added for each task and
    whether it introduces ambiguity.
4.  Consolidate Gemini and Groq results, comparing within-model changes
    against each model’s own full-schema baseline. Token counts across
    providers/models may not be directly comparable.
5.  Add another model or broaden the benchmark only after the failure
    audit.

## Expanding the scope: schemas

The current one-tool benchmark is useful for controlled ablations but
limits conclusions about tool diversity. Possible future schema
families:

- **Search/filter:** query text, labels, date range, status, sort order,
  result limit.
- **Record lookup:** identifier, optional fields to include, output
  format.
- **Update/action:** target identifier, enumerated action, optional
  reason or metadata.

These are proposed future families, not existing implemented tools.

Schema-design principles:

- Include required and optional parameters.
- Where supported, vary string, integer, boolean, enum, array, and
  nested-object parameters.
- Include constraints that matter to the task, such as allowed values
  and numeric ranges.
- Make descriptions informative without simply repeating parameter
  names.
- Use overlapping or confusable fields only when ambiguity is part of
  the research question.
- Maintain one canonical full schema per tool and generate conditions
  from it mechanically.
- Version schemas rather than silently changing them after a run.
- Record which parameters are relevant per task and which irrelevant
  parameter is added.

For a multi-tool benchmark, separate schema-content effects from
tool-selection effects. If studying argument correctness after tool
selection, hold the candidate tool fixed or report tool selection
separately. If studying full tool selection, vary the number and
similarity of candidate tools deliberately.

## Expanding the scope: tasks

Add tasks that test distinct, pre-specified skills rather than simply
increasing the count.

Useful dimensions:

- Difficulty, defined before running the models
- Number of parameters needed
- Parameter types and constraints
- Whether enum/range constraints must be followed
- Sensitivity to an irrelevant disclosed field
- Ambiguous dates, filters, sorting, and limits
- Tool diversity, if expanding beyond `search_issues`
- Underspecified requests, only if the benchmark explicitly tests
  clarification behavior

### Illustrative task metadata

Keep the exact task-file structure compatible with
`src/schemas/task_loader.py` and the evaluator. The following is a
proposed example, **not a claim that the current loader accepts these
exact fields**:

``` json
{
  "task_id": "example_001",
  "tool_name": "search_issues",
  "description": "Find open issues labelled AUTH_FAILURE.",
  "difficulty": "easy",
  "relevant_parameters": ["q", "status", "labels"],
  "irrelevant_parameter_candidates": ["sort", "with_comments"],
  "expected_arguments": {
    "q": "AUTH_FAILURE",
    "status": "open",
    "labels": ["AUTH_FAILURE"]
  },
  "acceptable_arguments": [],
  "rationale": "The request specifies a query, status, and label."
}
```

### Task quality controls

- Define expected arguments and relevance annotations before model runs.
- Ensure each task is valid under the canonical full schema.
- Ensure each condition is generated mechanically from the same
  canonical schema.
- Document when an ablation deliberately removes information needed for
  correct arguments.
- Avoid near-duplicate tasks that inflate the apparent sample size.
- Keep a fixed benchmark version for model comparisons and version new
  tasks separately.
- Pilot the tasks to identify ambiguous prompts and evaluator mistakes
  before spending the full call budget.

## Reproducibility checklist

For every run, record:

- Experiment/config name and version
- Model ID and provider
- Run date/time
- Schema and task-file versions or hashes
- Temperature, reasoning effort, tool-choice settings, and other
  generation parameters
- Repetition count and retry policy
- API errors and completed trials
- Evaluator version
- Whether outputs are new, resumed, or appended

Use consistent settings across conditions within a model. Note
provider-specific token accounting and API behavior when comparing
models.

## References

- [Groq Tool Use
  Overview](https://console.groq.com/docs/tool-use/overview)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
