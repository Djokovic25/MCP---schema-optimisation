# Schema Ablation v2 — Component Ablation Experiment

## 1. Experiment status

**Status:** Completed  
**Experiment:** Schema information ablation  
**Model:** `gemini-3.1-flash-lite`  
**Tool:** `search_issues`  
**Schema:** `schemas/synthetic/search_issues_v2.json`  
**Tasks:** `tasks/schema_ablation_tasks_v2.json`  
**Calls:** 15 tasks × 7 schema conditions × 1 repetition = **105 model calls**

The experiment uses Gemini's native function-calling interface. The selected tool is supplied as a native function declaration, and the model is constrained to call that tool. The returned function name and structured arguments are evaluated rather than asking the model to simulate JSON in ordinary text.

Google's Gemini documentation describes function declarations as containing the function name, purpose/description, and parameter schema, including types, descriptions, enums, and required parameters. It also recommends validation because schema-compliant calls can still be semantically incorrect. 

## 2. Research question

> **How does schema granularity affect LLM tool-invocation correctness and context cost after tool selection, and is the minimum sufficient schema task-dependent?**

This experiment addresses the first part through controlled one-component-at-a-time schema ablation.

The experiment starts **after tool selection**. The model is given only the `search_issues` tool, so tool-selection accuracy is not being studied here.

## 3. Experimental setup

### Full schema

The realistic synthetic schema contains:

- tool name
- tool description
- parameter names
- parameter descriptions
- parameter types
- enum values
- numeric constraints (`minimum`, `maximum`)
- required parameters
- array item type
- `additionalProperties: false`

The task set contains 15 requests:

| Difficulty | Tasks | Purpose |
|---|---|---|
| Easy | E1–E5 | Single-parameter and simple type/enum behavior |
| Medium | M1–M5 | Multi-parameter, arrays, sorting and mixed types |
| Hard | H1–H5 | Temporal formatting, multiple filters and mixed constraints |

### Schema conditions

Each condition removes one information component from the full schema:

1. Full
2. − tool description
3. − parameter descriptions
4. − type
5. − enum
6. − constraints
7. − required

This is a **marginal ablation**: each reduced condition differs from the full schema by one component.

## 4. Evaluation

Each returned call is evaluated on:

1. **Tool correctness** — whether the returned function is `search_issues`.
2. **Schema validity** — whether the returned arguments validate against the original full parameter schema.
3. **Argument correctness** — whether the arguments match the task's expected arguments or an explicitly allowed equivalent.
4. **Task success** — all required checks pass.

Failure types are recorded, including:

- `wrong_tool`
- `schema_invalid`
- `arguments_incorrect`
- `no_function_call`
- `invalid_arguments_structure`

The evaluator validates against the **full/original schema**, not the ablated schema. This is intentional: removing information from the model's disclosure should not redefine what constitutes a valid invocation.

## 5. Results

### Task success by schema condition

| Condition | Successful tasks | Success rate |
|---|---:|---:|
| Full | 14 / 15 | 93.3% |
| − tool description | 13 / 15 | 86.7% |
| − parameter descriptions | 12 / 15 | 80.0% |
| − type | 11 / 15 | 73.3% |
| − enum | 14 / 15 | 93.3% |
| − constraints | 14 / 15 | 93.3% |
| − required | 11 / 15 | 73.3% |
| **Overall** | **89 / 105** | **84.8%** |

## 6. Observed failure patterns

### Full schema

**1 failure: H4**

The task requested:

- state = `closed`
- sort = `created_desc`
- with_comments = `true`
- limit = `50`

The model returned `limit = 5`.

This is a **baseline model failure**, because H4 also failed under every ablated condition. It should not be attributed to schema removal.

### − tool description

Two failures:

- **M1:** the model incorrectly added `labels = ["AUTH_FAILURES"]`.
- **H4:** the model again returned `limit = 5` and also produced `sort = "updated_desc"`.

The tool description therefore shows a small but non-zero effect in this single-tool setting.

### − parameter descriptions

Three failures:

- **M1:** extra `labels = ["AUTH_FAILURES"]`.
- **H1:** dates were returned as date-only strings instead of the required ISO-8601 timestamps.
- **H4:** `limit = 5`.

H1 is especially informative because the full schema explicitly described the timestamp format.

### − type

Four failures:

- **M1:** `labels = "AUTH_FAILURES"` instead of an array.
- **M3:** `labels = "security,backend"` instead of `["security", "backend"]`.
- **H2:** `labels = "security"` instead of `["security"]`.
- **H4:** `limit = 5`.

The array failures indicate that the model can preserve the semantic content while producing the wrong structural representation when type information is removed.

### − enum

Only H4 failed.

The current task set therefore provides **no observed marginal performance loss from removing enum information**.

This should not be interpreted as proof that enums are unnecessary in general; the present tasks may not sufficiently stress enum ambiguity.

### − constraints

Only H4 failed.

The current tasks use valid limits such as 20 and 50, both inside the original `[1, 100]` range. Therefore the model does not need the min/max bounds to construct any tested answer.

### − required

Four failures:

- **M1:** missing `q` and extra `labels = ["AUTH_FAILURES"]`.
- **M5:** missing `q` and extra `labels = ["AUTH_FAILURES"]`.
- **H2:** missing `q` and extra `labels = ["AUTH_FAILURES"]`.
- **H4:** `limit = 5`.

The repeated omission of `q` after removing the `required` declaration is evidence that requiredness information can affect whether a core parameter is included.

## 7. Initial interpretation

The results suggest that schema components do **not** contribute equally to tool-invocation correctness.

The strongest observed effects in this benchmark are associated with:

- **type information**, particularly for array-valued parameters;
- **required information**, particularly for retaining mandatory parameters;
- **parameter descriptions**, particularly when descriptions encode semantic or formatting requirements.

In contrast:

- **enum information** produced no additional failures in this experiment;
- **numeric constraints** produced no additional failures;
- **tool description** had a smaller effect than parameter-level information.

A useful way to characterize the current result is:

> **The information needed to construct a correct tool invocation appears to depend on what the task requires from the schema.**

For example:

- An array-valued task can depend on `type`.
- A timestamp task can depend on the parameter description.
- A task with a mandatory search query can be affected by `required`.
- An ordinary task whose values already have obvious lexical mappings may not need enum or numeric-constraint information.

This is consistent with Gemini's documentation, which explicitly treats descriptions, strong typing, enums, and required parameters as parts of function declarations and recommends clear descriptions and strong typing. citeturn0search0turn0search2

## 8. Important limitations

### 8.1 One model

Only `gemini-3.1-flash-lite` has been evaluated so far. The findings should therefore be described as observations for this model and setup, not universal LLM behavior.

### 8.2 One tool

All tasks expose the same tool. Tool-selection effects are intentionally excluded.

### 8.3 One repetition

Each task-condition pair was run once. The results therefore estimate observed success on these 105 stochastic calls, but they do not yet provide stable repeated-trial success probabilities.

### 8.4 Easy-task ceiling effect

E1–E5 succeeded under every condition. These tasks are useful sanity checks but have limited discriminative power for schema ablation.

### 8.5 Marginal ablation only

Removing one component at a time does not identify the minimum sufficient schema. A component may be unnecessary alone but become important when another component is also absent.

### 8.6 Synthetic tasks

The tasks are designed synthetic requests. More diverse and realistic tool schemas are needed before making broader claims.

### 8.7 Baseline H4 failure

The 93.3% full-schema baseline includes a genuine H4 model error. It should be preserved rather than silently corrected or removed.

## 9. Provenance note

H5 required a wording correction during baseline validation.

The original wording created an ambiguity around whether the query should literally contain the token or its quoted form. After revising the task to:

> “Search issue titles and descriptions for the term AUTH_FAILURES, for issues assigned to alice, and include comments.”

the corrected H5 full-schema run succeeded.

Therefore the final reported full-schema baseline is:

> **14/15 = 93.3%**

with H5 documented as a corrected benchmark wording/re-run, rather than presenting the original H5 failure as a model failure.

## 10. What this experiment establishes

The experiment provides preliminary evidence that:

1. Schema information has a measurable effect on invocation correctness.
2. Different schema components affect different failure modes.
3. Type and required information produced the largest observed success-rate drops in this task set.
4. Parameter descriptions can matter when they carry semantic/formatting information.
5. Some schema components were redundant for the current tasks.
6. A full schema is not sufficient to guarantee a correct invocation: H4 failed even with the complete schema.

## 11. What it does not establish

It does **not** yet establish:

- the minimum sufficient schema for each task;
- a universal ordering of schema components by importance;
- that enum or constraints are generally unnecessary;
- that the observed percentages will hold across repetitions, models, tools, or domains;
- causal independence of schema components;
- the optimal task-aware disclosure policy.

## 12. Next experiment

The next stage should preserve this 105-call experiment and add repeated trials only after the benchmark is considered stable.

Recommended progression:

1. Repeat the 15 × 7 experiment for multiple repetitions.
2. Report confidence intervals / uncertainty around success rates.
3. Add targeted enum tasks where the natural-language request is ambiguous without the allowed-value set.
4. Add boundary/constraint tasks where min/max information is genuinely needed.
5. Add more difficult parameter-name/semantic mapping cases.
6. Run cumulative/combinatorial ablations to study the **schema sufficiency frontier**.
7. Extend to multiple tools and domains.
8. Compare multiple LLMs.

The long-term objective is to determine whether schema disclosure can be made **task-dependent** rather than uniformly full-schema, while preserving acceptable invocation correctness and reducing context cost.
