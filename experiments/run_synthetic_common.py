
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv

from src.experiments.runner import run_trial
from src.schemas.disclosure_v2 import build_task_disclosure
from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks


PROJECT_ROOT = Path(__file__).resolve().parents[1]

CONFIGS = {
    "groq": PROJECT_ROOT / "configs" / "schema_disclosure_synthetic_groq.yaml",
    "gemini": PROJECT_ROOT / "configs" / "schema_disclosure_synthetic_gemini.yaml",
    "groq_qwen": (
    PROJECT_ROOT
    / "configs"
    / "schema_disclosure_synthetic_groq_qwen.yaml"
),
}


def atomic_save_json(path: Path, data: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    try:
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def load_json_list(path: Path) -> list:
    if not path.exists():
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {path}")
    return data


def log_error(path: Path, record: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()
        os.fsync(f.fileno())


def make_client(provider: str, model_name: str):
    if provider in ("groq", "groq_qwen"):
        from src.llm.groq_client import GroqClient
        return GroqClient(model=model_name)

    if provider == "gemini":
        from src.llm.gemini import GeminiClient
        return GeminiClient(model=model_name)

    raise ValueError(f"Unknown provider: {provider}")


def main(provider: str) -> None:
    if provider not in CONFIGS:
        raise ValueError(f"Provider must be one of {list(CONFIGS)}")

    load_dotenv(PROJECT_ROOT / ".env")

    import yaml

    config_path = CONFIGS[provider]
    with config_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)

    experiment = config["experiment"]["name"]
    model_name = config["model"]["name"]
    tasks_path = PROJECT_ROOT / config["tasks"]["path"]
    output_dir = PROJECT_ROOT / config["output"]["directory"]
    output_path = output_dir / "raw_results.json"
    errors_path = output_dir / "errors.jsonl"

    repetitions = config["execution"]["repetitions"]
    delay_seconds = config["execution"]["delay_seconds"]
    max_calls = config["execution"]["max_calls"]
    conditions = config["conditions"]

    tasks = load_tasks(tasks_path)

    # Validate paths and schemas before making any API calls.
    for task in tasks:
        schema_path = PROJECT_ROOT / task["schema_path"]

        if not schema_path.is_file():
            raise FileNotFoundError(
                f"Schema for task {task['id']} not found: {schema_path}"
            )

        schema = load_schema(schema_path)

        if schema["name"] != {
            "repository": "search_repositories",
            "files": "search_files",
            "database": "query_database",
        }[task["schema_family"]]:
            raise ValueError(
                f"Tool/schema mismatch for task {task['id']}: "
                f"{schema['name']}"
            )

        properties = schema["parameters"]["properties"]

        for parameter in task["relevant_parameters"]:
            if parameter not in properties:
                raise ValueError(
                    f"{task['id']}: unknown relevant parameter {parameter}"
                )

        if task.get("irrelevant_parameter") not in properties:
            raise ValueError(
                f"{task['id']}: unknown irrelevant parameter "
                f"{task.get('irrelevant_parameter')}"
            )

        # Check that expected arguments are compatible with the full schema.
        # Evaluation itself remains in run_trial().

    results = load_json_list(output_path)

    completed = {
        (r["task_id"], r["condition"], r["repetition"])
        for r in results
        if all(k in r for k in ("task_id", "condition", "repetition"))
    }

    client = make_client(provider, model_name)

    pending = [
        (task, condition, repetition)
        for task in tasks
        for condition in conditions
        for repetition in range(1, repetitions + 1)
        if (task["id"], condition["name"], repetition) not in completed
    ]

    print("=" * 65)
    print(f"Experiment: {experiment}")
    print(f"Provider: {provider}")
    print(f"Model: {model_name}")
    print(f"Tasks: {len(tasks)}")
    print(f"Conditions: {len(conditions)}")
    print(f"Repetitions: {repetitions}")
    print(f"Previously completed: {len(completed)}")
    print(f"Pending: {len(pending)}")
    print(f"Output: {output_path}")
    print("=" * 65)

    calls_made = 0

    for index, (task, condition, repetition) in enumerate(pending, 1):
        if calls_made >= max_calls:
            print(f"Reached max_calls={max_calls}.")
            break

        task_id = task["id"]
        condition_name = condition["name"]
        schema_path = PROJECT_ROOT / task["schema_path"]

        # Load the correct complete schema for this task.
        full_schema = load_schema(schema_path)

        try:
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
                raise ValueError(f"Unknown condition: {condition_name}")

        except Exception as exc:
            # Configuration errors are not model/API attempts.
            raise RuntimeError(
                f"Could not prepare {task_id}/{condition_name}: {exc}"
            ) from exc

        print(
            f"[{index}/{len(pending)}] {task_id} | "
            f"{task['schema_family']} | {condition_name} | rep={repetition}"
        )
        print(
            "  Disclosed parameters:",
            list(disclosed_schema["parameters"]["properties"]),
        )

        calls_made += 1

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

            results.append(asdict(result))
            atomic_save_json(output_path, results)
            completed.add((task_id, condition_name, repetition))

            print(
                f"  success={result.task_success} | "
                f"failure={result.failure_type} | "
                f"input_tokens={result.input_tokens} | "
                f"latency_ms={result.latency_ms}"
            )

        except Exception as exc:
            # Keep API/runtime errors separate from valid model responses.
            error_record = {
                "experiment": experiment,
                "task_id": task_id,
                "schema_family": task["schema_family"],
                "condition": condition_name,
                "model": model_name,
                "repetition": repetition,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            }
            log_error(errors_path, error_record)
            print(f"  ERROR: {type(exc).__name__}: {exc}")

        if index < len(pending) and delay_seconds > 0:
            time.sleep(delay_seconds)

    print("\nRun finished.")
    print(f"Successful trial records: {len(results)}")
    print(f"Output: {output_path}")
    print(f"API/runtime errors: {errors_path}")
    print(
        "Note: errors are logged separately and are not counted as "
        "successful trial records."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python -m experiments.run_synthetic_common groq|gemini")
    main(sys.argv[1].lower())
