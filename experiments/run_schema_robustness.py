#EXPERIMENT 3: Check robustness fo experiment 2 results

import json
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv

from src.llm.gemini import GeminiClient
from src.experiments.runner import run_trial
from src.schemas.loader import load_schema
from src.schemas.disclosure import build_task_disclosure
from src.schemas.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "schema_robustness_v1.yaml"

TARGET_TASKS = {"M2", "H1", "H2"}
VALID_CONDITIONS = {"relevant_only", "minimal_relevant"}


def load_config(path: Path) -> Dict[str, Any]:
    import yaml

    with open(path, "r") as f:
        return yaml.safe_load(f)


def load_completed_trials(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []

    with open(path, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")

    return data


def save_results(results: List[Dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = path.with_suffix(".tmp")

    with open(temporary_path, "w") as f:
        json.dump(results, f, indent=2)

    temporary_path.replace(path)


def trial_key(trial: Dict[str, Any]) -> Tuple[str, str, int]:
    return (
        trial["task_id"],
        trial["condition"],
        int(trial["repetition"]),
    )


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    config = load_config(CONFIG_PATH)

    experiment_name = config["experiment"]["name"]
    model_name = config["model"]["name"]

    full_schema = load_schema(
        PROJECT_ROOT / config["schema"]["path"]
    )
    all_tasks = load_tasks(
        PROJECT_ROOT / config["tasks"]["path"]
    )

    tasks = [
        task for task in all_tasks
        if task["id"] in TARGET_TASKS
    ]

    if {task["id"] for task in tasks} != TARGET_TASKS:
        raise ValueError(
            f"Expected tasks {sorted(TARGET_TASKS)}, "
            f"found {[task['id'] for task in tasks]}"
        )

    conditions = [
        condition["name"]
        for condition in config["conditions"]
    ]

    if set(conditions) != VALID_CONDITIONS:
        raise ValueError(
            f"Expected conditions {sorted(VALID_CONDITIONS)}, "
            f"found {conditions}"
        )

    repetitions = int(config["execution"]["repetitions"])
    delay_seconds = float(
        config["execution"].get("delay_seconds", 0)
    )
    max_calls = config["execution"].get("max_calls")

    if repetitions != 5:
        raise ValueError("This experiment is configured for 5 repetitions.")

    expected_calls = len(tasks) * len(conditions) * repetitions

    if expected_calls != 30:
        raise ValueError(
            f"Expected 30 trials, calculated {expected_calls}."
        )

    output_dir = PROJECT_ROOT / config["output"]["directory"]
    output_path = output_dir / "raw_results.json"

    results = load_completed_trials(output_path)
    completed_keys = {trial_key(trial) for trial in results}

    expected_keys = {
        (task["id"], condition, repetition)
        for task in tasks
        for condition in conditions
        for repetition in range(1, repetitions + 1)
    }

    unexpected_keys = completed_keys - expected_keys

    if unexpected_keys:
        raise ValueError(
            "Existing output contains trials outside this experiment: "
            f"{sorted(unexpected_keys)}"
        )

    pending = [
        (task, condition, repetition)
        for task in tasks
        for condition in conditions
        for repetition in range(1, repetitions + 1)
        if (task["id"], condition, repetition) not in completed_keys
    ]

    print("=" * 65)
    print(f"Experiment: {experiment_name}")
    print(f"Model:      {model_name}")
    print(f"Tasks:      {[task['id'] for task in tasks]}")
    print(f"Conditions: {conditions}")
    print(f"Repetitions per pair: {repetitions}")
    print(f"Expected total calls: {expected_calls}")
    print(f"Already completed:    {len(completed_keys)}")
    print(f"Pending calls:        {len(pending)}")
    print(f"Output: {output_path}")
    print("=" * 65)

    if not pending:
        print("All trials are already complete.")
        return

    client = GeminiClient(model=model_name)
    calls_made = 0

    for index, (task, condition, repetition) in enumerate(
        pending, start=1
    ):
        if max_calls is not None and calls_made >= max_calls:
            print(f"Reached max_calls={max_calls}.")
            break

        disclosed_schema = build_task_disclosure(
            schema=full_schema,
            relevant_parameters=task["relevant_parameters"],
            condition=condition,
        )

        print(
            f"[{index}/{len(pending)}] "
            f"{task['id']} | {condition} | repetition={repetition}"
        )

        print(
            "  Disclosed parameters:",
            list(disclosed_schema["parameters"]["properties"].keys()),
        )

        # The full schema remains the evaluation reference.
        # Only the disclosed schema is sent to the model.
        result = run_trial(
            experiment=experiment_name,
            task=task,
            tool_schema=full_schema,
            disclosed_schema=disclosed_schema,
            condition=condition,
            client=client,
            model_name=model_name,
            repetition=repetition,
        )

        results.append(asdict(result))
        save_results(results, output_path)
        calls_made += 1

        print(f"  Success: {result.task_success}")
        print(f"  Input tokens: {result.input_tokens}")
        print(f"  Latency: {result.latency_ms:.2f} ms")
        print()

        if delay_seconds > 0 and index < len(pending):
            time.sleep(delay_seconds)

    print("=" * 65)
    print(f"Calls made this run: {calls_made}")
    print(f"Trials saved:        {len(results)} / {expected_calls}")
    print(f"Results: {output_path}")
    print("=" * 65)


if __name__ == "__main__":
    main()