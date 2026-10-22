from pathlib import Path
import json
import sys
from collections import Counter
from jsonschema import Draft202012Validator, FormatChecker
ROOT = Path(__file__).resolve().parent

TASK_FILE = ROOT / "tasks" / "14_new_tasks.json"

SCHEMAS = {
    "repository": ROOT / "schemas" / "synthetic" / "repository_search_v1.json",
    "files": ROOT / "schemas" / "synthetic" / "file_search_v1.json",
    "database": ROOT / "schemas" / "synthetic" / "database_query_v1.json",
}

def load_json(path):
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def check_schema_file(path):
    schema = load_json(path)

    # Check that the schema itself is structurally valid.
    Draft202012Validator.check_schema(schema)

    if not schema.get("name"):
        raise ValueError("Missing schema name")

    parameters = schema.get("parameters", {})
    if parameters.get("type") != "object":
        raise ValueError("parameters.type must be object")

    properties = parameters.get("properties", {})
    required = parameters.get("required", [])

    for name in required:
        if name not in properties:
            raise ValueError(
                f"Required parameter '{name}' is not defined"
            )

    print(f"  Schema valid: {path.name}")
    print(f"  Tool name: {schema['name']}")
    print(f"  Parameters: {len(properties)}")

    return schema


def check_task(task, schemas, errors):
    task_id = task.get("id", "<missing ID>")
    family = task.get("schema_family")
    schema = schemas.get(family)

    if schema is None:
        errors.append(
            f"{task_id}: unknown schema_family {family!r}"
        )
        return

    parameters = schema["parameters"]
    properties = parameters.get("properties", {})
    expected = task.get("expected_arguments")

    if not isinstance(expected, dict):
        errors.append(
            f"{task_id}: expected_arguments must be an object"
        )
        return

    # Validate expected arguments against the full schema.
    validator = Draft202012Validator(
        parameters,
        format_checker=FormatChecker(),
    )

    for error in validator.iter_errors(expected):
        location = ".".join(str(p) for p in error.absolute_path)
        location = location or "<arguments>"
        errors.append(
            f"{task_id}: invalid expected arguments at "
            f"{location}: {error.message}"
        )

    # Check task parameter references.
    relevant = task.get("relevant_parameters", [])
    irrelevant = task.get("irrelevant_parameter")

    if not isinstance(relevant, list):
        errors.append(
            f"{task_id}: relevant_parameters must be a list"
        )
        return

    unknown_relevant = set(relevant) - set(properties)
    if unknown_relevant:
        errors.append(
            f"{task_id}: unknown relevant parameters "
            f"{sorted(unknown_relevant)}"
        )

    if len(relevant) != len(set(relevant)):
        errors.append(
            f"{task_id}: duplicate relevant parameters"
        )

    if set(expected) != set(relevant):
        errors.append(
            f"{task_id}: expected argument keys "
            f"{sorted(expected)} do not match relevant_parameters "
            f"{sorted(relevant)}"
        )

    if irrelevant is not None:
        if irrelevant not in properties:
            errors.append(
                f"{task_id}: irrelevant_parameter "
                f"{irrelevant!r} is not in the schema"
            )

        if irrelevant in relevant:
            errors.append(
                f"{task_id}: irrelevant parameter is also relevant"
            )

        if irrelevant in expected:
            errors.append(
                f"{task_id}: irrelevant parameter appears "
                "in expected_arguments"
            )

    # Verify the recorded schema path refers to the expected family.
    schema_path = task.get("schema_path", "")
    if schema_path:
        expected_schema_path = (
         Path("schemas") / "synthetic" / SCHEMAS[family].name
    )

    actual_schema_path = Path(schema_path)

    if actual_schema_path.name != expected_schema_path.name:
        errors.append(
            f"{task_id}: schema_path {schema_path!r} does not "
            f"match {expected_schema_path.as_posix()!r}"
        )


def main():
    errors = []

    print("Checking schema files...")
    schemas = {}

    for family, path in SCHEMAS.items():
        try:
            schemas[family] = check_schema_file(path)
        except Exception as exc:
            errors.append(f"{family}: cannot load/check schema: {exc}")

    if len(schemas) != len(SCHEMAS):
        print("\nCannot check tasks until all schemas load.")
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("\nChecking task file...")
    tasks = load_json(TASK_FILE)

    if not isinstance(tasks, list):
        print("ERROR: task file must contain a JSON array.")
        sys.exit(1)

    ids = [task.get("id") for task in tasks]
    
    counts = Counter(ids)
    duplicates = {
        task_id: count
        for task_id, count in counts.items()
        if count > 1
    }

    if duplicates:
        errors.append(f"Duplicate task IDs: {duplicates}")
    
    # Check that repeated IDs do not hide conflicting task definitions.
    tasks_by_id = {}
    for task in tasks:
        task_id = task.get("id")
        if task_id in tasks_by_id and task != tasks_by_id[task_id]:
            errors.append(
                f"{task_id}: duplicate ID has conflicting task content"
            )
        tasks_by_id[task_id] = task

    unique_tasks = list(tasks_by_id.values())
    
    for task in unique_tasks:
        check_task(task, schemas, errors)

    print(f"Records in file: {len(tasks)}")
    print(f"Unique task IDs: {len(unique_tasks)}")
    print(f"Duplicate IDs: {len(duplicates)}")

    print("\nUnique tasks by schema family:")
    for family in SCHEMAS:
        count = sum(
            task.get("schema_family") == family
            for task in unique_tasks
        )
        print(f"  {family}: {count}")

    if errors:
        print(f"\nFAILED: {len(errors)} issue(s) found.")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print("\nPASSED: all unique tasks match their schemas.")
    

if __name__ == "__main__":
    main()