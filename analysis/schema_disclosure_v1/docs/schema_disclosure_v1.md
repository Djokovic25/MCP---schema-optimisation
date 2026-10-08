# Experiment 2 — Task-Conditioned Schema Disclosure

## 1. Objective

This experiment investigates whether an LLM can perform correct tool invocation when it is given only the schema information relevant to the current task, rather than the complete schema of the selected tool.

The experiment starts **after tool selection**.

The research question is:

> **Can task-conditioned parameter disclosure reduce schema context cost while preserving LLM tool-invocation correctness?**

A secondary question is:

> **How much semantic schema information is required once irrelevant parameters have been removed?**

This distinguishes two factors:

1. **Parameter scope** — whether irrelevant parameters are disclosed.
2. **Schema richness** — whether semantic information such as parameter descriptions and constraints is retained.

---

## 2. Experimental Setting

### Model

* Model: `gemini-3.1-flash-lite`
* API: Google Gemini native function calling
* Function calling mode: `ANY`
* Allowed function: only the selected tool
* Automatic function calling: disabled
* Repetitions: 1

Gemini function calling exposes a function declaration containing the function name, description, parameters, and related schema information. The model returns a structured function call containing the selected function and its arguments.

Because the experiment restricts the allowed function to the target tool, the experiment does **not** evaluate tool selection.

The evaluation begins with the assumption:

> **The correct tool has already been selected.**

---

## 3. Tool

The benchmark uses a synthetic `search_issues` tool.

The full schema contains nine parameters:

```text
q
state
assignee
labels
created_after
created_before
sort
limit
with_comments
```

The schema contains multiple types of information:

* Tool name
* Tool description
* Parameter names
* Parameter types
* Parameter descriptions
* Enum values
* Array item types
* Required parameters
* Numeric constraints

This provides a realistic schema with both structural and semantic information.

---

## 4. Dataset

The experiment uses the same 15 tasks from Experiment 1.

Tasks are divided into three difficulty levels:

| Difficulty | Tasks |
| ---------- | ----- |
| Easy       | E1–E5 |
| Medium     | M1–M5 |
| Hard       | H1–H5 |

Each task contains:

* Natural-language task description
* Expected function name
* Expected arguments
* Optional acceptable arguments
* Difficulty
* `relevant_parameters`
* One controlled `irrelevant_parameter`

The `relevant_parameters` field is **benchmark metadata only**.

It is used by the experiment runner to construct the disclosed schema and is **never shown to the model**.

---

## 5. Experimental Conditions

Four schema-disclosure conditions were evaluated.

### 5.1 Full

The complete tool schema is provided.

```text
All 9 parameters
+
All available schema metadata
```

This is the baseline condition.

---

### 5.2 Relevant Only

Only the parameters relevant to the current task are disclosed.

However, each retained parameter keeps its complete metadata:

* Parameter name
* Type
* Description
* Enum
* Array item type
* Numeric constraints

The tool description is also retained.

The `required` list is filtered to contain only retained parameters.

Conceptually:

```text
Full schema
    ↓
Remove irrelevant parameters
    ↓
Keep all metadata for remaining parameters
```

This condition tests whether **irrelevant parameters can be removed without reducing invocation correctness**.

---

### 5.3 Relevant + One Irrelevant

The task-relevant parameters are disclosed together with one explicitly selected irrelevant parameter.

The irrelevant parameter is controlled by the benchmark rather than randomly sampled.

For example:

```text
Relevant:
q, state, assignee

Additional irrelevant parameter:
limit
```

The additional parameter retains its complete schema metadata.

This condition tests whether adding a small amount of irrelevant schema information changes:

* Invocation correctness
* Context cost
* Latency

It also provides a controlled intermediate condition between relevant-only and the full schema.

---

### 5.4 Minimal Relevant

Only the task-relevant parameters are disclosed, but semantic schema information is reduced.

Retained:

* Tool name
* Parameter names
* Parameter types
* Array item types
* Enum values
* Required parameters

Removed:

* Tool description
* Parameter descriptions
* Numeric constraints such as `minimum` and `maximum`

This condition is therefore a **minimal structural schema**, not the absolute minimum schema possible.

Conceptually:

```text
Full schema
    ↓
Keep only relevant parameters
    ↓
Remove descriptions and numeric constraints
    ↓
Retain structural information
```

---

## 6. Condition Comparison

| Condition               | Parameters   | Descriptions | Types | Enums | Constraints | Required |
| ----------------------- | ------------ | ------------ | ----- | ----- | ----------- | -------- |
| Full                    | All          | ✓            | ✓     | ✓     | ✓           | ✓        |
| Relevant only           | Relevant     | ✓            | ✓     | ✓     | ✓           | ✓        |
| Relevant + 1 irrelevant | Relevant + 1 | ✓            | ✓     | ✓     | ✓           | ✓        |
| Minimal relevant        | Relevant     | ✗            | ✓     | ✓     | ✗           | ✓        |

The experiment therefore separates:

### Parameter scope

```text
Full
vs.
Relevant only
```

and:

### Schema richness

```text
Relevant only
vs.
Minimal relevant
```

---

## 7. Experimental Design

Number of tasks:

```text
15
```

Number of conditions:

```text
4
```

Repetitions:

```text
1
```

Total API calls:

```text
15 × 4 × 1 = 60
```

The same task is evaluated under all four conditions, making this a matched within-task comparison.

---

## 8. Evaluation

A trial is considered successful only when the generated function invocation satisfies the evaluator's expected function and argument requirements.

The evaluator checks:

* Function name
* Argument names
* Argument values
* Required arguments
* Expected argument structure
* Acceptable alternative arguments where defined

The experiment therefore evaluates **invocation correctness**, rather than merely whether the model produced syntactically valid JSON.

---

# 9. Results

## 9.1 Overall Results

| Condition               | Success | Success Rate | Mean Input Tokens | Median Input Tokens | Mean Latency |
| ----------------------- | ------: | -----------: | ----------------: | ------------------: | -----------: |
| Full                    |   14/15 |        93.3% |            368.20 |                 363 |   1834.87 ms |
| Relevant only           |   14/15 |        93.3% |            166.60 |                 146 |   2270.43 ms |
| Relevant + 1 irrelevant |   14/15 |        93.3% |            197.00 |                 179 |   2992.02 ms |
| Minimal relevant        |   11/15 |        73.3% |             87.27 |                  82 |   1843.11 ms |

---

## 9.2 Input Token Reduction

Compared with the full condition:

| Condition               | Mean Input Tokens | Reduction vs Full |
| ----------------------- | ----------------: | ----------------: |
| Full                    |            368.20 |                 — |
| Relevant only           |            166.60 |         **55.1%** |
| Relevant + 1 irrelevant |            197.00 |         **46.8%** |
| Minimal relevant        |             87.27 |         **76.5%** |

The relevant-only condition therefore reduced mean input tokens by approximately **55%** while maintaining the same observed success rate as the full schema.

The minimal-relevant condition reduced mean input tokens by approximately **76.5%**, but its success rate decreased from 93.3% to 73.3%.

---

## 9.3 Results by Difficulty

| Difficulty | Full | Relevant Only | +1 Irrelevant | Minimal Relevant |
| ---------- | ---: | ------------: | ------------: | ---------------: |
| Easy       |  5/5 |           5/5 |           5/5 |              5/5 |
| Medium     |  5/5 |           5/5 |           5/5 |              4/5 |
| Hard       |  4/5 |           4/5 |           4/5 |              2/5 |

The relevant-only condition preserved the full-schema performance at every difficulty level in this experiment.

The minimal-relevant condition performed perfectly on the easy tasks but showed failures on medium and hard tasks.

---

# 10. Per-Task Results

| Task | Full | Relevant Only | +1 Irrelevant | Minimal Relevant |
| ---- | ---- | ------------- | ------------- | ---------------- |
| E1   | ✓    | ✓             | ✓             | ✓                |
| E2   | ✓    | ✓             | ✓             | ✓                |
| E3   | ✓    | ✓             | ✓             | ✓                |
| E4   | ✓    | ✓             | ✓             | ✓                |
| E5   | ✓    | ✓             | ✓             | ✓                |
| M1   | ✓    | ✓             | ✓             | ✓                |
| M2   | ✓    | ✓             | ✓             | ✗                |
| M3   | ✓    | ✓             | ✓             | ✓                |
| M4   | ✓    | ✓             | ✓             | ✓                |
| M5   | ✓    | ✓             | ✓             | ✓                |
| H1   | ✓    | ✓             | ✓             | ✗                |
| H2   | ✓    | ✓             | ✓             | ✗                |
| H3   | ✓    | ✓             | ✓             | ✓                |
| H4   | ✗    | ✗             | ✗             | ✗                |
| H5   | ✓    | ✓             | ✓             | ✓                |

---

# 11. Failure Analysis

There were four task-level failures in the minimal-relevant condition:

* M2
* H1
* H2
* H4

However, H4 also failed under all other conditions and therefore needs to be treated separately.

---

## 11.1 M2 — Argument Decomposition Failure

### Expected

The task required separate parameters including:

```text
q = AUTH_FAILURES
state = closed
```

### Minimal-relevant output

The model generated:

```text
q = "AUTH_FAILURES state:closed"
with_comments = true
limit = 20
```

The model therefore understood the task semantics but represented part of the requested filtering operation inside the `q` parameter instead of using the dedicated `state` parameter.

### Interpretation

This is an **argument decomposition / representation failure**.

The structural schema told the model that parameters such as `q` and `state` existed, but removing their semantic descriptions appears to have made the distinction between their intended roles less clear.

The model effectively compressed multiple pieces of intent into the query string.

This suggests that parameter names and types alone may not always be sufficient for correctly mapping natural-language intent onto multiple semantically related parameters.

---

# 11.2 H1 — Date Representation Failure

### Expected

The task required:

```text
created_after  = 2026-01-01T00:00:00Z
created_before = 2026-02-01T00:00:00Z
```

### Minimal-relevant output

The model generated:

```text
created_after  = 2026-01-01
created_before = 2026-02-01
```

The semantic values were correct, but the required representation was incomplete.

### Interpretation

This is a **value-format representation failure**.

The model correctly identified:

* which parameters to use
* the relevant dates
* the temporal relationship

but failed to preserve the required ISO-8601 timestamp representation.

The full/relevant-only schema retained parameter descriptions, which provide semantic information about expected value representation.

This failure therefore provides evidence that parameter descriptions can carry information that is not captured by the structural type alone.

---

# 11.3 H2 — Complex Date Representation Failure

H2 is a more complex task involving:

```text
q
state
assignee
labels
created_after
created_before
limit
```

The minimal-relevant condition again generated date-only values instead of the expected ISO-8601 timestamps.

The other major arguments were correctly represented.

### Interpretation

This reproduces the same failure pattern as H1 in a more complex task.

The important observation is that the model did not generally fail to understand the task.

Instead, it failed specifically on the **representation format of temporal values**.

This strengthens the interpretation that semantic parameter descriptions can matter even when the parameter names and types remain available.

---

# 11.4 H4 — Intrinsic Baseline Failure

H4 failed under every condition.

The full schema generated:

```text
limit = 5
```

instead of the expected:

```text
limit = 50
```

The same issue appeared in the relevant-only and relevant-plus-one-irrelevant conditions.

Therefore H4 cannot be cleanly attributed to schema reduction.

The minimal-relevant condition additionally produced a less structured query representation, but the baseline failure already existed with the full schema.

### Interpretation

H4 is treated as an **intrinsic model/task failure** rather than evidence that schema disclosure caused the failure.

This distinction is important because otherwise the minimal-relevant condition could incorrectly be blamed for a failure that was already present in the baseline.

---

# 12. Main Findings

## Finding 1 — Irrelevant parameter removal did not reduce observed correctness

The full and relevant-only conditions both achieved:

```text
14/15 = 93.3%
```

However:

```text
Full:
368.20 mean input tokens

Relevant only:
166.60 mean input tokens
```

This represents approximately:

```text
55.1% reduction in mean input tokens
```

with no observed loss in task success on this benchmark.

### Interpretation

For this model, tool, and task set, a large portion of the complete schema was not necessary for the observed invocation decisions when the task-relevant parameters were retained with their semantic metadata.

---

## Finding 2 — One irrelevant parameter increased context cost without changing observed accuracy

The relevant-plus-one-irrelevant condition achieved:

```text
14/15 = 93.3%
```

the same success rate as the full and relevant-only conditions.

However, its mean input token count increased from:

```text
166.60
```

to:

```text
197.00
```

relative to relevant-only.

This corresponds to approximately 30 additional mean input tokens for one controlled irrelevant parameter.

### Interpretation

In this benchmark, the additional irrelevant parameter increased schema/context size without producing an observable accuracy benefit.

Because only one irrelevant parameter was added and the parameter itself varied by task, this result should be treated as preliminary rather than generalized.

---

## Finding 3 — Removing semantic metadata caused a substantial accuracy drop

The minimal-relevant condition achieved:

```text
11/15 = 73.3%
```

compared with:

```text
14/15 = 93.3%
```

for relevant-only.

At the same time, minimal-relevant reduced mean input tokens to:

```text
87.27
```

or approximately:

```text
76.5% below the full condition
```

### Interpretation

The experiment suggests that the important distinction is not simply:

> more schema vs less schema

Instead, the results indicate that **which information is removed matters**.

Removing irrelevant parameters while retaining semantic descriptions preserved observed correctness.

Removing semantic information such as parameter descriptions produced failures involving:

* argument decomposition
* value representation
* complex task execution

---

# 13. Central Experimental Pattern

The experiment produces the following three-level pattern:

```text
                    Mean Input      Success
Full                368 tokens      93.3%
Relevant only       167 tokens      93.3%
Minimal relevant     87 tokens      73.3%
```

This suggests a useful distinction between:

### Parameter redundancy

Information about parameters that are irrelevant to the current task.

and:

### Semantic schema information

Information that helps the model understand how a parameter should be interpreted and how values should be represented.

The first can potentially be removed substantially.

The second appears more difficult to remove without affecting correctness.

---

# 14. Interpretation

The current evidence supports the following statement:

> **Task-conditioned parameter disclosure can substantially reduce context cost while preserving invocation correctness, but semantic schema information remains important for complex tasks.**

More specifically:

* Removing irrelevant parameters reduced context substantially.
* Retaining descriptions and structural metadata preserved observed performance.
* Removing descriptions and constraints produced a noticeable drop in correctness.
* The resulting failures were subtle rather than simple schema violations.
* The failures primarily involved mapping natural-language intent into the correct parameter representation.

This suggests that schema reduction should not be treated as a binary question of whether the schema is "needed."

Instead, schema components appear to have different informational roles.

---

# 15. Relationship to Experiment 1

Experiment 1 and Experiment 2 answer different questions.

## Experiment 1 — Component Ablation

Experiment 1 asked:

> **What happens when individual schema components are removed globally?**

Conditions included removing:

* Tool description
* Parameter descriptions
* Type
* Enum
* Constraints
* Required

Experiment 1 found that:

* Parameter descriptions affected formatting and semantic interpretation.
* Type affected structural representations such as arrays.
* Required affected multi-parameter tasks.
* Enum and constraints had little observed effect in this task set.
* Tool description had a smaller effect in the single-tool setup.

---

## Experiment 2 — Task-Conditioned Disclosure

Experiment 2 asks:

> **Can irrelevant parameters be removed on a task-by-task basis while retaining the information necessary for correct invocation?**

The key comparison is:

```text
Full schema
        ↓
Remove irrelevant parameters
        ↓
Retain semantic metadata
```

This produced:

```text
93.3% → 93.3%
```

while reducing mean input tokens by:

```text
55.1%
```

The second comparison is:

```text
Relevant parameters
        ↓
Remove semantic metadata
        ↓
Retain structural schema
```

This produced:

```text
93.3% → 73.3%
```

Thus, Experiment 2 complements Experiment 1 by examining **schema scope** rather than only **schema component importance**.

---

# 16. Limitations

Several limitations should be considered before drawing broader conclusions.

### 16.1 Single model

Only:

```text
gemini-3.1-flash-lite
```

was evaluated.

The results therefore do not establish that other LLMs will behave similarly.

---

### 16.2 Single tool

All tasks use the same:

```text
search_issues
```

tool.

Different tool domains may produce different schema requirements.

---

### 16.3 Small task set

Only 15 tasks were evaluated.

The results are therefore useful as an initial controlled experiment rather than a statistically robust benchmark.

---

### 16.4 One repetition

Each task-condition pair was evaluated once.

Model stochasticity cannot therefore be separated from the effect of schema condition.

Interesting effects should be repeated in subsequent experiments.

---

### 16.5 Minimal-relevant is not the absolute minimum schema

The minimal-relevant condition deliberately retains:

* parameter types
* enum values
* array item types
* required parameters

Therefore it should be described as:

> **minimal structural schema**

rather than:

> **minimum sufficient schema**

---

### 16.6 Token measurements

The recorded input token count is the model/API-reported prompt token count.

It includes the overall request context and schema representation.

A future analysis should separately measure the serialized schema token cost itself to isolate the contribution of schema disclosure more precisely.

---

### 16.7 Latency

Latency was recorded but should not currently be treated as a primary finding.

The observed mean latency did not decrease monotonically with schema size:

```text
Full                     1834.87 ms
Relevant only            2270.43 ms
Relevant + 1 irrelevant  2992.02 ms
Minimal relevant         1843.11 ms
```

Therefore this experiment does **not** provide evidence that schema reduction reduces API latency.

---

### 16.8 H4 baseline failure

H4 failed even with the full schema.

It should therefore not be used as clean evidence that minimal schema caused an invocation failure.

---

# 17. Next Experiment

The most informative next step is targeted repetition of the clean minimal-schema failures.

Candidate tasks:

```text
M2
H1
H2
```

These represent distinct failure modes:

| Task | Failure Mode                                |
| ---- | ------------------------------------------- |
| M2   | Argument decomposition                      |
| H1   | Date/value representation                   |
| H2   | Date/value representation in a complex task |

The recommended comparison is:

```text
Relevant only
vs.
Minimal relevant
```

with multiple repetitions per task.

For example:

```text
3 tasks
×
2 conditions
×
5 repetitions
=
30 additional API calls
```

If the same failure patterns recur, the evidence that semantic schema information affects invocation correctness becomes substantially stronger.

H4 should be analyzed separately because its baseline already fails.

---

# 18. Current Research Hypothesis

Based on Experiments 1 and 2, the working hypothesis is:

> **Schema information has heterogeneous value for tool invocation: irrelevant parameters can often be removed with substantial context savings, while semantic metadata that explains parameter meaning and value representation may remain necessary for complex tasks.**

This motivates a more granular research direction:

> **Instead of asking whether an LLM needs the full tool schema, determine the minimum task-sufficient subset of schema information required for correct invocation.**

---

# 19. Summary

Experiment 2 evaluated four schema disclosure strategies over 15 tasks and 60 native function-calling trials.

The key results were:

```text
Full
14/15 = 93.3%
368.20 mean input tokens

Relevant only
14/15 = 93.3%
166.60 mean input tokens
55.1% reduction

Relevant + one irrelevant
14/15 = 93.3%
197.00 mean input tokens
46.8% reduction

Minimal relevant
11/15 = 73.3%
87.27 mean input tokens
76.5% reduction
```

The main empirical observation is:

> **Removing irrelevant parameters preserved observed invocation correctness while substantially reducing context cost.**

However:

> **Removing semantic schema information produced failures in argument decomposition and value representation, particularly on medium and hard tasks.**

The experiment therefore suggests that effective schema optimization may require **task-conditioned disclosure that preserves semantically important schema components rather than indiscriminately minimizing the schema.**

---

## Reproducibility

Configuration:

```text
configs/schema_disclosure_v1.yaml
```

Tasks:

```text
tasks/schema_disclosure_tasks_v1.json
```

Experiment runner:

```text
experiments/run_schema_disclosure.py
```

Schema construction:

```text
src/schemas/disclosure.py
```

Raw results:

```text
results/schema_disclosure_v1/raw_results.json
```

The experiment can be rerun with:

```bash
python experiments/run_schema_disclosure.py
```
