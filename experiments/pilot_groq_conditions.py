
import json
import time
from pathlib import Path

from dotenv import load_dotenv

from src.llm.groq_client import GroqClient
from src.experiments.runner import run_trial
from src.schemas.disclosure import build_task_disclosure

# Adjust these two imports if your project uses different loader paths.
from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

MODEL = "openai/gpt-oss-20b"
CONDITIONS = [
    "full",
    "relevant_only",
    "relevant_plus_one_irrelevant",
    "minimal_relevant",
]

schema = load_schema(
    PROJECT_ROOT / "schemas/synthetic/search_issues_v2.json"
)
tasks = load_tasks(
    PROJECT_ROOT / "tasks/schema_disclosure_tasks_v1.json"
)
task = next(t for t in tasks if t["id"] == "E1")
client = GroqClient(model=MODEL)

results = []

for condition in CONDITIONS:
    if condition == "full":
        disclosed_schema = schema
    else:
        disclosed_schema = build_task_disclosure(
            schema=schema,
            relevant_parameters=task["relevant_parameters"],
            condition=condition,
            irrelevant_parameter=task.get("irrelevant_parameter"),
        )

    result = run_trial(
        experiment="groq_condition_pilot",
        task=task,
        tool_schema=schema,
        disclosed_schema=disclosed_schema,
        condition=condition,
        client=client,
        model_name=MODEL,
        repetition=1,
    )

    record = vars(result)
    results.append(record)

    print(
        f"{condition}: success={result.task_success}, "
        f"failure={result.failure_type}, "
        f"input_tokens={result.input_tokens}, "
        f"latency_ms={result.latency_ms:.1f}"
    )

    time.sleep(2)

output_path = (
    PROJECT_ROOT / "results" / "groq_condition_pilot.json"
)
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(results, indent=2))

print(f"\nSaved {len(results)} records to {output_path}")
