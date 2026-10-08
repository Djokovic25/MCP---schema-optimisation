# import json
# import time
# from pathlib import Path

# import yaml
# from dotenv import load_dotenv

# from src.experiments.runner import run_trial
# from src.llm.gemini import GeminiClient
# from src.schemas.disclosure import build_ablation
# from src.schemas.loader import load_schema
# from src.schemas.task_loader import load_tasks


# def load_config(path: str):
#     with open(path, "r", encoding="utf-8") as f:
#         return yaml.safe_load(f)


# def save_result(path: Path, result):
#     record = {
#         "experiment": result.experiment,
#         "task_id": result.task_id,
#         "condition": result.condition,
#         "model": result.model,
#         "repetition": result.repetition,

#         "function_name": result.function_name,
#         "arguments": result.arguments,

#         "tool_correct": result.tool_correct,
#         "schema_valid": result.schema_valid,
#         "arguments_correct": result.arguments_correct,
#         "task_success": result.task_success,
#         "failure_type": result.failure_type,

#         "input_tokens": result.input_tokens,
#         "output_tokens": result.output_tokens,
#         "latency_ms": result.latency_ms,
#     }

#     with path.open("a", encoding="utf-8") as f:
#         f.write(json.dumps(record) + "\n")


# def main():

#     load_dotenv()

#     config = load_config(
#         "configs/schema_ablation.yaml"
#     )

#     experiment_name = config["experiment"]["name"]
#     model_name = config["model"]["name"]

#     schema = load_schema(
#         config["schema"]["path"]
#     )

#     tasks = load_tasks(
#         config["tasks"]["path"]
#     )

#     conditions = config["conditions"]

#     max_tasks = config["execution"].get(
#         "max_tasks",
#         len(tasks)
#     )

#     max_conditions = config["execution"].get(
#         "max_conditions",
#         len(conditions)
#     )

#     tasks = tasks[:max_tasks]
#     conditions = conditions[:max_conditions]

#     repetitions = config["execution"]["repetitions"]
#     delay_seconds = config["execution"]["delay_seconds"]
#     max_calls = config["execution"]["max_calls"]

#     output_dir = Path(
#         config["output"]["directory"]
#     )

#     output_dir.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     output_file = output_dir / "raw_results.jsonl"

#     total_calls = (
#         len(tasks)
#         * len(conditions)
#         * repetitions
#     )

#     print("=" * 70)
#     print("SCHEMA ABLATION EXPERIMENT")
#     print("=" * 70)
#     print(f"Experiment:       {experiment_name}")
#     print(f"Model:            {model_name}")
#     print(f"Tasks:            {len(tasks)}")
#     print(f"Conditions:       {len(conditions)}")
#     print(f"Repetitions:      {repetitions}")
#     print(f"Total calls:      {total_calls}")
#     print(f"Maximum allowed:  {max_calls}")
#     print(f"Delay:            {delay_seconds}s")
#     print(f"Output:           {output_file}")
#     print("=" * 70)

#     if total_calls > max_calls:
#         raise ValueError(
#             f"Experiment requires {total_calls} calls, "
#             f"but max_calls is {max_calls}."
#         )

#     client = GeminiClient(
#         model=model_name
#     )

#     completed = 0

#     for repetition in range(1, repetitions + 1):

#         print()
#         print(
#             f"========== REPETITION "
#             f"{repetition}/{repetitions} =========="
#         )

#         for task in tasks:

#             for condition in conditions:

#                 condition_name = condition["name"]

#                 removed_components = condition[
#                     "removed_components"
#                 ]

#                 disclosed_schema = build_ablation(
#                     schema=schema,
#                     removed_components=removed_components,
#                 )

#                 print()
#                 print(
#                     f"[{completed + 1}/{total_calls}] "
#                     f"Task={task['id']} "
#                     f"Condition={condition_name} "
#                     f"Repetition={repetition}"
#                 )

#                 result = run_trial(
#                     experiment=experiment_name,
#                     task=task,
#                     tool_schema=schema,
#                     disclosed_schema=disclosed_schema,
#                     condition=condition_name,
#                     client=client,
#                     model_name=model_name,
#                     repetition=repetition,
#                 )

#                 save_result(
#                     output_file,
#                     result,
#                 )

#                 completed += 1

#                 print(
#                     f"  Function: {result.function_name}"
#                 )

#                 print(
#                     f"  Arguments: {result.arguments}"
#                 )

#                 print(
#                     f"  Success: {result.task_success}"
#                 )

#                 print(
#                     f"  Failure: {result.failure_type}"
#                 )

#                 print(
#                     f"  Input tokens: {result.input_tokens}"
#                 )

#                 print(
#                     f"  Output tokens: {result.output_tokens}"
#                 )

#                 if result.latency_ms is not None:
#                     print(
#                         f"  Latency (ms): "
#                         f"{result.latency_ms:.2f}"
#                     )
#                 else:
#                     print(
#                         "  Latency (ms): None"
#                     )

#                 if completed < total_calls:
#                     time.sleep(delay_seconds)

#     print()
#     print("=" * 70)
#     print("EXPERIMENT COMPLETE")
#     print("=" * 70)
#     print(f"Completed calls: {completed}")
#     print(f"Results saved to: {output_file}")


# if __name__ == "__main__":
#     main()


#continuing from 17
import json
import random
import time
from pathlib import Path

import yaml
from dotenv import load_dotenv
from google.genai import errors

from src.experiments.runner import run_trial
from src.llm.gemini import GeminiClient
# from src.schemas.disclosure import build_ablation
from src.schemas.disclosure import (
    build_ablation,
    build_task_disclosure,
)
from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks


def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_result(path: Path, result):
    record = {
        "experiment": result.experiment,
        "task_id": result.task_id,
        "condition": result.condition,
        "model": result.model,
        "repetition": result.repetition,

        "function_name": result.function_name,
        "arguments": result.arguments,

        "tool_correct": result.tool_correct,
        "schema_valid": result.schema_valid,
        "arguments_correct": result.arguments_correct,
        "task_success": result.task_success,
        "failure_type": result.failure_type,

        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "latency_ms": result.latency_ms,
    }

    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def load_completed_trials(path: Path):
    """
    Load the identity of trials already completed.

    A trial is uniquely identified by:
        task_id + condition + repetition
    """

    completed = set()

    if not path.exists():
        return completed

    with path.open("r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if not line:
                continue

            record = json.loads(line)

            key = (
                record["task_id"],
                record["condition"],
                record["repetition"],
            )

            completed.add(key)

    return completed


def run_trial_with_retry(
    experiment,
    task,
    tool_schema,
    disclosed_schema,
    condition,
    client,
    model_name,
    repetition,
    max_retries=3,
):
    """
    Run one experimental trial.

    Only transient server-side errors are retried.

    The retry attempts do not create additional experimental
    result records. Only a successful model response becomes
    one TrialResult.
    """

    for attempt in range(max_retries + 1):

        try:

            return run_trial(
                experiment=experiment,
                task=task,
                tool_schema=tool_schema,
                disclosed_schema=disclosed_schema,
                condition=condition,
                client=client,
                model_name=model_name,
                repetition=repetition,
            )

        except errors.ServerError as exc:

            status_code = getattr(
                exc,
                "status_code",
                None,
            )

            if status_code is None:
                status_code = getattr(
                    exc,
                    "code",
                    None,
                )

            is_transient = (
                isinstance(status_code, int)
                and status_code >= 500
            )

            if not is_transient:
                raise

            if attempt >= max_retries:
                print()
                print(
                    "  Server error persisted after "
                    f"{max_retries} retries."
                )
                raise

            delay = min(
                60,
                5 * (2 ** attempt)
            )

            jitter = random.uniform(
                0,
                2
            )

            total_delay = delay + jitter

            print()
            print(
                f"  Transient server error "
                f"{status_code}."
            )

            print(
                f"  Retrying in "
                f"{total_delay:.1f}s "
                f"(attempt "
                f"{attempt + 1}/{max_retries})"
            )

            time.sleep(total_delay)


def main():

    load_dotenv()

    config = load_config(
        "configs/schema_ablation.yaml"
    )

    experiment_name = config["experiment"]["name"]
    model_name = config["model"]["name"]

    schema = load_schema(
        config["schema"]["path"]
    )

    tasks = load_tasks(
        config["tasks"]["path"]
    )

    conditions = config["conditions"]

    max_tasks = config["execution"].get(
        "max_tasks",
        len(tasks)
    )

    max_conditions = config["execution"].get(
        "max_conditions",
        len(conditions)
    )

    tasks = tasks[:max_tasks]
    conditions = conditions[:max_conditions]

    repetitions = config["execution"]["repetitions"]
    delay_seconds = config["execution"]["delay_seconds"]
    max_calls = config["execution"]["max_calls"]

    output_dir = Path(
        config["output"]["directory"]
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = output_dir / "raw_results.jsonl"

    total_calls = (
        len(tasks)
        * len(conditions)
        * repetitions
    )

    completed_trials = load_completed_trials(
        output_file
    )

    remaining_calls = (
        total_calls - len(completed_trials)
    )

    print("=" * 70)
    print("SCHEMA ABLATION EXPERIMENT")
    print("=" * 70)

    print(
        f"Experiment:       {experiment_name}"
    )

    print(
        f"Model:            {model_name}"
    )

    print(
        f"Tasks:            {len(tasks)}"
    )

    print(
        f"Conditions:       {len(conditions)}"
    )

    print(
        f"Repetitions:      {repetitions}"
    )

    print(
        f"Total planned:    {total_calls}"
    )

    print(
        f"Already complete: {len(completed_trials)}"
    )

    print(
        f"Remaining:        {remaining_calls}"
    )

    print(
        f"Maximum allowed:  {max_calls}"
    )

    print(
        f"Delay:            {delay_seconds}s"
    )

    print(
        f"Output:           {output_file}"
    )

    print("=" * 70)

    if total_calls > max_calls:
        raise ValueError(
            f"Experiment requires {total_calls} calls, "
            f"but max_calls is {max_calls}."
        )

    if len(completed_trials) > total_calls:
        raise ValueError(
            "Existing results contain more completed "
            "trials than the configured experiment."
        )

    if remaining_calls == 0:

        print()
        print(
            "All planned trials are already complete."
        )

        return

    client = GeminiClient(
        model=model_name
    )

    completed_this_run = 0

    for repetition in range(
        1,
        repetitions + 1
    ):

        print()
        print(
            f"========== REPETITION "
            f"{repetition}/{repetitions} =========="
        )

        for task in tasks:

            for condition in conditions:

                condition_name = condition["name"]

                trial_key = (
                    task["id"],
                    condition_name,
                    repetition,
                )

                if trial_key in completed_trials:

                    print()
                    print(
                        f"SKIPPING completed trial: "
                        f"Task={task['id']} "
                        f"Condition={condition_name} "
                        f"Repetition={repetition}"
                    )

                    continue

                removed_components = condition[
                    "removed_components"
                ]

                disclosed_schema = build_ablation(
                    schema=schema,
                    removed_components=removed_components,
                )

                current_number = (
                    len(completed_trials)
                    + completed_this_run
                    + 1
                )

                print()
                print(
                    f"[{current_number}/{total_calls}] "
                    f"Task={task['id']} "
                    f"Condition={condition_name} "
                    f"Repetition={repetition}"
                )

                result = run_trial_with_retry(
                    experiment=experiment_name,
                    task=task,
                    tool_schema=schema,
                    disclosed_schema=disclosed_schema,
                    condition=condition_name,
                    client=client,
                    model_name=model_name,
                    repetition=repetition,
                )

                save_result(
                    output_file,
                    result,
                )

                completed_trials.add(
                    trial_key
                )

                completed_this_run += 1

                print(
                    f"  Function: "
                    f"{result.function_name}"
                )

                print(
                    f"  Arguments: "
                    f"{result.arguments}"
                )

                print(
                    f"  Success: "
                    f"{result.task_success}"
                )

                print(
                    f"  Failure: "
                    f"{result.failure_type}"
                )

                print(
                    f"  Input tokens: "
                    f"{result.input_tokens}"
                )

                print(
                    f"  Output tokens: "
                    f"{result.output_tokens}"
                )

                if result.latency_ms is not None:

                    print(
                        f"  Latency (ms): "
                        f"{result.latency_ms:.2f}"
                    )

                else:

                    print(
                        "  Latency (ms): None"
                    )

                if (
                    len(completed_trials)
                    < total_calls
                ):

                    time.sleep(
                        delay_seconds
                    )

    print()
    print("=" * 70)
    print("EXPERIMENT COMPLETE")
    print("=" * 70)

    print(
        f"Total completed: "
        f"{len(completed_trials)}"
    )

    print(
        f"Results saved to: "
        f"{output_file}"
    )


if __name__ == "__main__":
    main()