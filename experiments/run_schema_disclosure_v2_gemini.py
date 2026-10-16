#EXPERIMENT 2: SCHEMA DISCLOSURE
import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List
import os
from dotenv import load_dotenv

from src.llm.gemini import GeminiClient
from src.experiments.runner import run_trial
from src.schemas.loader import load_schema
from src.schemas.disclosure import build_task_disclosure
from src.schemas.task_loader import load_tasks
from src.schemas.disclosure_v2 import build_task_disclosure

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# CONFIG_PATH = PROJECT_ROOT / "configs" / "schema_disclosure_rigorous.yaml"
CONFIG_PATH = (
    PROJECT_ROOT
    / "configs"
    / "schema_disclosure_v2_gemini.yaml"
)

def load_config(path: Path) -> Dict[str, Any]:
    import yaml

    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_result(result: Any, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    serializable_results = [
        asdict(trial) if not isinstance(trial, dict) else trial
        for trial in result
    ]

    temp_path = output_path.with_suffix(output_path.suffix + ".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(serializable_results, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, output_path)

    finally:
        if temp_path.exists():
            temp_path.unlink()

def load_completed_trials(output_path: Path) -> List[Dict[str, Any]]:
    if not output_path.exists():
        return []

    with open(output_path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        return []

    return data


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    config = load_config(CONFIG_PATH)

    experiment_name = config["experiment"]["name"]
    model_name = config["model"]["name"]

    schema_path = PROJECT_ROOT / config["schema"]["path"]
    tasks_path = PROJECT_ROOT / config["tasks"]["path"]

    # output_directory = PROJECT_ROOT / config["output"]["directory"]
    # output_path = output_directory / "raw_results.json"
    output_directory = PROJECT_ROOT / config["output"]["directory"]
    output_path = output_directory / "raw_results.json"

    repetitions = config["execution"]["repetitions"]
    delay_seconds = config["execution"]["delay_seconds"]
    max_calls = config["execution"].get("max_calls")

    full_schema = load_schema(schema_path)
    tasks = load_tasks(tasks_path)
    conditions = config["conditions"]

    client = GeminiClient(model=model_name)

    completed_trials = load_completed_trials(output_path)

    completed_keys = {
        (
            trial["task_id"],
            trial["condition"],
            trial["repetition"],
        )
        for trial in completed_trials
    }

    results = completed_trials.copy()

    pending_trials = []

    for task in tasks:
        for condition in conditions:
            for repetition in range(1, repetitions + 1):

                key = (
                    task["id"],
                    condition["name"],
                    repetition,
                )

                if key in completed_keys:
                    continue

                pending_trials.append(
                    (task, condition, repetition)
                )

    total_pending = len(pending_trials)

    print()
    print("=" * 70)
    print(f"Experiment : {experiment_name}")
    print(f"Model      : {model_name}")
    print(f"Tasks      : {len(tasks)}")
    print(f"Conditions : {len(conditions)}")
    print(f"Repetitions: {repetitions}")
    print(f"Completed  : {len(completed_trials)}")
    print(f"Pending    : {total_pending}")
    print("=" * 70)
    print()

    calls_made = 0

    for index, (task, condition, repetition) in enumerate(
        pending_trials,
        start=1,
    ):

        if max_calls is not None and calls_made >= max_calls:
            print()
            print(f"Reached max_calls={max_calls}. Stopping.")
            break

        condition_name = condition["name"]

        # ---------------------------------------------------------
        # Construct the schema shown to the LLM
        # ---------------------------------------------------------

        if condition_name == "full":

            disclosed_schema = full_schema

        elif condition_name == "relevant_only":

            disclosed_schema = build_task_disclosure(
                schema=full_schema,
                relevant_parameters=task["relevant_parameters"],
                condition="relevant_only",
            )

        elif condition_name == "relevant_plus_one_irrelevant":

            disclosed_schema = build_task_disclosure(
                schema=full_schema,
                relevant_parameters=task["relevant_parameters"],
                condition="relevant_plus_one_irrelevant",
                irrelevant_parameter=task["irrelevant_parameter"],
            )

        elif condition_name == "minimal_relevant":

            disclosed_schema = build_task_disclosure(
                schema=full_schema,
                relevant_parameters=task["relevant_parameters"],
                condition="minimal_relevant",
            )

        else:
            raise ValueError(
                f"Unknown condition: {condition_name}"
            )

        # ---------------------------------------------------------
        # Display trial information
        # ---------------------------------------------------------

        print(
            f"[{index}/{total_pending}] "
            f"Task={task['id']} | "
            f"Condition={condition_name} | "
            f"Repetition={repetition}"
        )

        print(
            "  Relevant parameters:",
            task.get("relevant_parameters", []),
        )

        print(
            "  Disclosed parameters:",
            list(
                disclosed_schema["parameters"]["properties"].keys()
            ),
        )

        # ---------------------------------------------------------
        # Run trial
        # ---------------------------------------------------------

        result = run_trial(
            experiment=experiment_name,
            task=task,
            tool_schema=full_schema,
            disclosed_schema=disclosed_schema,
            condition=condition_name,
            client=client,
            model_name=model_name,
            repetition=repetition,
        )

        results.append(result)

        calls_made += 1

        # Save after every trial so an interrupted experiment
        # can resume without losing completed API calls.
        save_result(
            results,
            output_path,
        )

        print(
            f"  Success: {result.task_success}"
        )

        print(
            f"  Input tokens: {result.input_tokens}"
        )

        print(
            f"  Latency: {result.latency_ms:.2f} ms"
        )

        print()

        if (
            delay_seconds > 0
            and index < total_pending
        ):
            time.sleep(delay_seconds)

    print()
    print("=" * 70)
    print("Experiment complete")
    print("=" * 70)

    print(
        f"Results saved to:\n{output_path}"
    )

    print(
        f"Total stored trials: {len(results)}"
    )


if __name__ == "__main__":
    main()