
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.experiments.runner import run_trial
from src.llm.groq_client import GroqClient
from src.schemas.disclosure_v2 import build_task_disclosure
from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "configs" / "schema_disclosure_v2_groq.yaml"


def atomic_save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(data, indent=2))
    temp_path.replace(path)


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    with CONFIG_PATH.open() as f:
        config = yaml.safe_load(f)

    experiment = config["experiment"]["name"]
    model_name = config["model"]["name"]

    schema_path = PROJECT_ROOT / config["schema"]["path"]
    tasks_path = PROJECT_ROOT / config["tasks"]["path"]
    output_dir = PROJECT_ROOT / config["output"]["directory"]

    output_path = output_dir / "raw_results.json"
    errors_path = output_dir / "errors.jsonl"

    
    repetitions = config["execution"]["repetitions"]
    delay_seconds = config["execution"]["delay_seconds"]
    max_calls = config["execution"]["max_calls"]
    max_tasks = config["execution"]["max_tasks"]
    max_conditions = config["execution"]["max_conditions"]

    full_schema = load_schema(schema_path)
    tasks = load_tasks(tasks_path)[:max_tasks]
    conditions = config["conditions"][:max_conditions]

    client = GroqClient(model=model_name)

    # Load existing results to support safe resumption.
    if output_path.exists():
        results = json.loads(output_path.read_text())
    else:
        results = []

    completed = {
        (r["task_id"], r["condition"], r["repetition"])
        for r in results
    }

    attempted_this_run = 0

    print(f"Experiment: {experiment}")
    print(f"Model: {model_name}")
    print(f"Tasks: {len(tasks)}")
    print(f"Conditions: {len(conditions)}")
    print(f"Repetitions: {repetitions}")
    print(f"Existing completed trials: {len(completed)}")

    for task in tasks:
        for condition_config in conditions:
            condition_name = condition_config["name"]

            for repetition in range(1, repetitions + 1):
                key = (task["id"], condition_name, repetition)

                if key in completed:
                    continue

                if attempted_this_run >= max_calls:
                    print("Reached max_calls for this run.")
                    print(f"Results saved to: {output_path}")
                    return

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

                attempted_this_run += 1

                try:
                    result = run_trial(
                        experiment=experiment,
                        task=task,
                        tool_schema=full_schema,
                        disclosed_schema=disclosed_schema,
                        condition=condition_name,
                        client=client,
                        model_name=model_name,
                        repetition=repetition,
                    )

                    record = vars(result)
                    results.append(record)
                    completed.add(key)
                    atomic_save_json(output_path, results)

                    print(
                        f"{task['id']} | {condition_name} | "
                        f"rep={repetition} | "
                        f"success={result.task_success} | "
                        f"failure={result.failure_type} | "
                        f"input_tokens={result.input_tokens} | "
                        f"latency_ms={result.latency_ms:.1f}"
                    )

                except Exception as exc:
                    error_record = {
                        "experiment": experiment,
                        "task_id": task["id"],
                        "condition": condition_name,
                        "model": model_name,
                        "repetition": repetition,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "timestamp_utc": datetime.now(
                            timezone.utc
                        ).isoformat(),
                    }

                    output_dir.mkdir(parents=True, exist_ok=True)
                    with errors_path.open("a") as f:
                        f.write(json.dumps(error_record) + "\n")

                    print(
                        f"ERROR | {task['id']} | {condition_name} | "
                        f"rep={repetition} | "
                        f"{type(exc).__name__}: {exc}"
                    )

                time.sleep(delay_seconds)

    print("\nRun finished.")
    print(f"Completed trials: {len(completed)}")
    print(f"Results saved to: {output_path}")
    print(f"API errors logged to: {errors_path}")


if __name__ == "__main__":
    main()
