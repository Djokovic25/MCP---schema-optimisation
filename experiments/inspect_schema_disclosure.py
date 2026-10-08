import json
from pathlib import Path
from typing import Any, Dict

from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks
from src.schemas.disclosure import build_task_disclosure


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCHEMA_PATH = PROJECT_ROOT / "schemas/synthetic/search_issues_v2.json"
TASKS_PATH = PROJECT_ROOT / "tasks/schema_disclosure_tasks_v1.json"


def print_schema_summary(
    condition: str,
    schema: Dict[str, Any],
) -> None:

    parameters = schema["parameters"]["properties"]
    required = schema["parameters"].get("required", [])

    print(f"\n  Condition: {condition}")
    print(f"  Parameters: {list(parameters.keys())}")
    print(f"  Required: {required}")

    print("  Parameter details:")

    for name, details in parameters.items():
        print(f"    - {name}")

        print(
            f"      type: {details.get('type')}"
        )

        if "items" in details:
            print(
                f"      items.type: "
                f"{details['items'].get('type')}"
            )

        if "enum" in details:
            print(
                f"      enum: {details['enum']}"
            )

        print(
            f"      description: "
            f"{'present' if 'description' in details else 'absent'}"
        )

        constraints = []

        if "minimum" in details:
            constraints.append(
                f"minimum={details['minimum']}"
            )

        if "maximum" in details:
            constraints.append(
                f"maximum={details['maximum']}"
            )

        print(
            f"      constraints: "
            f"{', '.join(constraints) if constraints else 'none'}"
        )

    print(
        f"  Tool description: "
        f"{'present' if 'description' in schema else 'absent'}"
    )


def build_condition_schema(
    full_schema: Dict[str, Any],
    task: Dict[str, Any],
    condition: str,
) -> Dict[str, Any]:

    if condition == "full":

        return full_schema

    if condition == "relevant_only":

        return build_task_disclosure(
            schema=full_schema,
            relevant_parameters=task["relevant_parameters"],
            condition="relevant_only",
        )

    if condition == "relevant_plus_one_irrelevant":

        return build_task_disclosure(
            schema=full_schema,
            relevant_parameters=task["relevant_parameters"],
            condition="relevant_plus_one_irrelevant",
            irrelevant_parameter=task["irrelevant_parameter"],
        )

    if condition == "minimal_relevant":

        return build_task_disclosure(
            schema=full_schema,
            relevant_parameters=task["relevant_parameters"],
            condition="minimal_relevant",
        )

    raise ValueError(
        f"Unknown condition: {condition}"
    )


def main():

    full_schema = load_schema(SCHEMA_PATH)
    tasks = load_tasks(TASKS_PATH)

    conditions = [
        "full",
        "relevant_only",
        "relevant_plus_one_irrelevant",
        "minimal_relevant",
    ]

    print()
    print("=" * 80)
    print("Experiment 2 — Schema Disclosure Inspection")
    print("=" * 80)
    print(f"Schema: {SCHEMA_PATH}")
    print(f"Tasks : {TASKS_PATH}")
    print(f"Tasks : {len(tasks)}")
    print()

    for task in tasks:

        print()
        print("-" * 80)
        print(f"Task: {task['id']}")
        print("-" * 80)

        print(
            f"Description: {task['description']}"
        )

        print(
            f"Relevant parameters: "
            f"{task['relevant_parameters']}"
        )

        print(
            f"Irrelevant parameter: "
            f"{task['irrelevant_parameter']}"
        )

        for condition in conditions:

            disclosed_schema = build_condition_schema(
                full_schema=full_schema,
                task=task,
                condition=condition,
            )

            print_schema_summary(
                condition=condition,
                schema=disclosed_schema,
            )

    print()
    print("=" * 80)
    print("Inspection complete — no API calls were made.")
    print("=" * 80)


if __name__ == "__main__":
    main()