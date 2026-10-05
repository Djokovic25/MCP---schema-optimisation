import os

from dotenv import load_dotenv

from src.evaluation.evaluator import evaluate_response
from src.llm.gemini import GeminiClient
from src.llm.prompts import build_tool_invocation_prompt
from src.schemas.disclosure import build_disclosure
from src.schemas.loader import load_schema
from src.schemas.task_loader import load_tasks


def main():

    # Load environment variables
    load_dotenv()

    # -----------------------------
    # Configuration
    # -----------------------------

    model_name = os.getenv("GEMINI_MODEL")

    if not model_name:
        raise ValueError(
            "GEMINI_MODEL was not found in the environment."
        )

    schema_path = "schemas/synthetic/zentrax_lookup.json"
    tasks_path = "tasks/pilot_tasks.json"

    task_id = "T1"

    # We already ran T1 with the "name" condition.
    # Run only the remaining two conditions.
    disclosure_conditions = [
        "parameters",
        "full",
    ]

    # -----------------------------
    # Load components
    # -----------------------------

    schema = load_schema(schema_path)
    tasks = load_tasks(tasks_path)

    task = next(
        task for task in tasks
        if task["id"] == task_id
    )

    # -----------------------------
    # Create LLM client
    # -----------------------------

    client = GeminiClient(
        model=model_name,
    )

    # -----------------------------
    # Run each disclosure condition
    # -----------------------------

    for disclosure_condition in disclosure_conditions:

        # -----------------------------
        # Build disclosed schema
        # -----------------------------

        disclosed_schema = build_disclosure(
            schema,
            disclosure_condition,
        )

        # -----------------------------
        # Build prompt
        # -----------------------------

        prompt = build_tool_invocation_prompt(
            task_description=task["description"],
            disclosed_schema=disclosed_schema,
        )

        # -----------------------------
        # Call model
        # -----------------------------

        response = client.generate(prompt)

        # -----------------------------
        # Evaluate response
        # -----------------------------

        evaluation = evaluate_response(
            raw_response=response.raw_text,
            tool_schema=schema,
            expected_arguments=task["expected_arguments"],
            expected_tool=schema["name"],
        )

        # -----------------------------
        # Print results
        # -----------------------------

        print("=" * 70)
        print("PILOT TRIAL")
        print("=" * 70)

        print("MODEL:", model_name)
        print("TASK:", task_id)
        print("CONDITION:", disclosure_condition)

        print()
        print("DISCLOSED SCHEMA:")
        print(disclosed_schema)

        print()
        print("MODEL RESPONSE:")
        print(response.raw_text)

        print()
        print("USAGE:")
        print("INPUT TOKENS:", response.input_tokens)
        print("OUTPUT TOKENS:", response.output_tokens)
        print("LATENCY (ms):", response.latency_ms)

        print()
        print("EVALUATION:")
        print("JSON VALID:", evaluation.json_valid)
        print("TOOL CORRECT:", evaluation.tool_correct)
        print("SCHEMA VALID:", evaluation.schema_valid)
        print("ARGUMENTS CORRECT:", evaluation.arguments_correct)
        print("TASK SUCCESS:", evaluation.task_success)
        print("FAILURE TYPE:", evaluation.failure_type)

        print()


if __name__ == "__main__":
    main()