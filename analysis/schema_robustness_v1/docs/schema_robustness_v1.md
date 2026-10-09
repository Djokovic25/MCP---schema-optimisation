# Experiment 3A: Robustness of Minimal-Schema Failures

## 1. Objective

Experiment 3A investigates whether argument-construction failures observed under the `minimal_relevant` schema condition in Experiment 2 are repeatable.

The central question is:

> Do tasks that fail under a minimal structural schema continue to fail across repeated model calls, while the same tasks succeed when semantic schema metadata is retained?

This experiment is a targeted robustness check. It does not estimate the general success rate of minimal schemas across arbitrary tasks.

## 2. Experimental Setup

| Setting      | Value                               |
| ------------ | ----------------------------------- |
| Experiment   | `schema_robustness_v1`              |
| Model        | `gemini-3.1-flash-lite`             |
| Tool         | `search_issues`                     |
| Benchmark    | `schema_disclosure_tasks_v1.json`   |
| Schema       | `search_issues_v2.json`             |
| Target tasks | M2, H1, H2                          |
| Conditions   | `relevant_only`, `minimal_relevant` |
| Repetitions  | 5 per task-condition pair           |
| Total trials | 30                                  |

The three tasks were selected because they exhibited argument-correctness failures under `minimal_relevant` in Experiment 2.

Each task was evaluated under both schema conditions for five repetitions, giving:

$$
3 \times 2 \times 5 = 30 \text{ trials}
$$

The task prompt and task definition were held constant between conditions. The schema condition was the intended experimental variable.

## 3. Schema Conditions

### 3.1 Relevant-only

The model received only the parameters identified as relevant to the task. Their descriptions and the other metadata retained by this condition were preserved.

This condition reduces the number of exposed parameters while retaining semantic information about how to use them.

### 3.2 Minimal-relevant

The model received the same task-relevant parameter set, retaining structural information such as parameter names, types, array item types, applicable enums, and required-field information.

The tool description, parameter descriptions, and numeric constraints were removed.

This condition tests whether the retained structural information is sufficient for correct argument construction on the selected tasks.

**Important:** The conditions differ in multiple metadata components. Therefore, this experiment does not isolate the individual causal contribution of parameter descriptions, tool descriptions, or numeric constraints.

## 4. Evaluation Metrics

The experiment records:

* **Tool correctness:** Whether the model selected the expected tool.
* **Schema validity:** Whether the generated arguments passed the schema-related validation.
* **Argument correctness:** Whether the generated arguments matched the task's expected arguments.
* **Task success:** Whether the trial satisfied the evaluator's success criteria.
* **Input tokens:** API-reported input-token count.
* **Output tokens:** API-reported output-token count.
* **Latency:** Recorded request latency in milliseconds.

A schema-valid function call can still be semantically incorrect. For example, placing a status filter inside the search query may produce a valid string while failing the task's expected argument mapping.

## 5. Results

### 5.1 Task-level success

| Task      |    Relevant-only | Minimal-relevant |
| --------- | ---------------: | ---------------: |
| M2        |       5/5 (100%) |         0/5 (0%) |
| H1        |       5/5 (100%) |         0/5 (0%) |
| H2        |       5/5 (100%) |         0/5 (0%) |
| **Total** | **15/15 (100%)** |    **0/15 (0%)** |

All 30 calls selected `search_issues` and were marked schema-valid. All 15 relevant-only calls were argument-correct, whereas all 15 minimal-relevant calls were argument-incorrect.

These results establish a consistent difference between the two conditions on the selected tasks. They do not establish that the same success rates will hold on other tasks.

### 5.2 Input-token cost

| Task                  | Relevant-only | Minimal-relevant | Reduction |
| --------------------- | ------------: | ---------------: | --------: |
| M2                    |           201 |              103 |     48.8% |
| H1                    |           172 |               82 |     52.3% |
| H2                    |           317 |              163 |     48.6% |
| **Mean across tasks** |     **230.0** |        **116.0** | **49.6%** |

The values are consistent across repetitions for each task-condition pair.

These are API-reported total input-token counts, not isolated measurements of serialized schema size. They should therefore be interpreted as observed input-token costs under this setup.

Latency varied considerably between calls and did not establish a reliable latency advantage for either condition.

## 6. Failure Analysis

### 6.1 M2: Query and state decomposition

The task requires the search term and issue state to be supplied as separate arguments.

Expected arguments:

```json
{
  "q": "AUTH_FAILURES",
  "state": "closed",
  "with_comments": true,
  "limit": 20
}
```

All five relevant-only calls produced the expected argument mapping.

All five minimal-relevant calls failed argument correctness:

* Three calls included `AUTH_FAILURES state:closed` in `q`.
* Two calls included `AUTH_FAILURES is:issue is:closed` in `q`.

The model consistently represented the status filter within the query instead of supplying the expected separate `state` argument.

This is an argument-representation failure, not a tool-selection failure or a basic JSON-validity failure.

### 6.2 H1: Timestamp representation

The task requires a date range with ISO-8601 timestamps.

Expected values:

```json
{
  "created_after": "2026-01-01T00:00:00Z",
  "created_before": "2026-02-01T00:00:00Z"
}
```

All five relevant-only calls returned the expected timestamps.

All five minimal-relevant calls returned date-only strings:

```json
{
  "created_after": "2026-01-01",
  "created_before": "2026-02-01"
}
```

The calendar dates were correct, but the generated values did not match the expected timestamp representation.

This illustrates that satisfying a parameter's string type does not guarantee that the value satisfies the task's formatting requirements.

### 6.3 H2: Multi-parameter argument construction

H2 requires the model to map several constraints to separate parameters, including a query, date range, assignee, label, state, and result limit.

All five relevant-only calls were correct.

All five minimal-relevant calls failed. Each returned date-only strings instead of the expected ISO-8601 timestamps. One repetition also included `AUTH_FAILURES` in the `labels` array, although that value belonged in the search query.

This task exhibits a repeated timestamp-representation error and one additional field-mapping error.

## 7. Interpretation

The experiment supports three observations.

1. **The selected failures were repeatable.** The M2, H1, and H2 failures observed under the minimal-relevant condition in Experiment 2 recurred in all five repetitions per task.

2. **The richer schema condition retained successful argument construction.** Relevant-only achieved 15/15 successes on these selected tasks, compared with 0/15 for minimal-relevant.

3. **The reduced input-token cost came with a correctness trade-off.** Minimal-relevant used approximately 49.6% fewer mean input tokens across the three tasks, but it failed all 15 trials.

The failure patterns suggest that structural schema information alone was insufficient for these tasks. Semantic metadata may help the model distinguish between query content and a dedicated state filter, or infer the required representation of timestamp values.

However, this experiment cannot establish which removed metadata component caused each failure. The results show an association between the schema condition and the observed outcomes, not a component-level causal explanation.

## 8. Relationship to Previous Experiments

### Experiment 1: Component ablation

Experiment 1 examined the effect of removing individual schema components. It provided initial evidence that schema components such as types, parameter descriptions, and required-field information can affect invocation correctness on the benchmark.

### Experiment 2: Task-conditioned disclosure

Experiment 2 compared full-schema disclosure, relevant-only disclosure, relevant parameters plus one irrelevant parameter, and minimal-relevant disclosure.

Relevant-only achieved 14/15 successes, matching the full-schema condition, while reducing mean input tokens by approximately 55.1%.

Minimal-relevant achieved 11/15 successes overall, with errors involving argument decomposition and timestamp representation.

### Experiment 3A: Robustness check

Experiment 3A repeated three tasks that had failed under minimal-relevant disclosure.

The results show that the selected failures recurred across all five repetitions per task, while relevant-only succeeded in all corresponding trials.

Together, the experiments motivate the hypothesis that task-conditioned schema disclosure can reduce context cost, but the semantic information required for correct invocation depends on the task.

## 9. Limitations

* Only three tasks were included.
* The tasks were selected because they had already failed under the minimal-relevant condition.
* Only one model was evaluated.
* Five repetitions per condition provide limited evidence about broader stochastic behavior.
* Multiple metadata components were removed together, preventing component-level attribution.
* The benchmark uses a synthetic tool and does not establish generalization to real-world MCP servers or other tools.
* Input-token counts represent the API-reported total, not schema-only token usage.
* The experiment evaluates generated arguments against benchmark expectations; it does not establish whether executing those arguments against a live issue tracker would return the intended results.

## 10. Conclusion

Experiment 3A demonstrates repeatable argument-correctness failures under minimal-relevant schema disclosure for three selected tasks. Relevant-only disclosure succeeded in all corresponding repetitions while using approximately 49.6% fewer mean input tokens across those tasks.

The results support further investigation of task-dependent schema sufficiency: reducing schema size may preserve correctness when useful semantic metadata remains available, whereas removing too much metadata may impair argument construction on particular tasks.

The next experimental step should isolate the contributions of parameter descriptions, tool descriptions, and constraints, ideally by changing one component at a time on tasks that exhibit the corresponding failure modes.
