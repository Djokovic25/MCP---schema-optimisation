import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from jsonschema import ValidationError, validate


@dataclass
class EvaluationResult:
    json_valid: bool
    tool_correct: bool
    schema_valid: bool
    arguments_correct: bool
    task_success: bool
    failure_type: Optional[str]


def evaluate_response(
    raw_response: str,
    tool_schema: Dict[str, Any],
    expected_arguments: Dict[str, Any],
    expected_tool: str,
) -> EvaluationResult:

    # ---------------------------------------------------------
    # 1. JSON validity
    # ---------------------------------------------------------

    try:
        response = json.loads(raw_response)
    except (json.JSONDecodeError, TypeError):
        return EvaluationResult(
            json_valid=False,
            tool_correct=False,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="invalid_json",
        )

    # ---------------------------------------------------------
    # 2. Basic response structure
    # ---------------------------------------------------------

    if not isinstance(response, dict):
        return EvaluationResult(
            json_valid=True,
            tool_correct=False,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="invalid_response_structure",
        )

    tool_name = response.get("tool")
    arguments = response.get("arguments")

    if not isinstance(arguments, dict):
        return EvaluationResult(
            json_valid=True,
            tool_correct=(tool_name == expected_tool),
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="invalid_arguments_structure",
        )

    # ---------------------------------------------------------
    # 3. Tool correctness
    # ---------------------------------------------------------

    tool_correct = tool_name == expected_tool

    if not tool_correct:
        return EvaluationResult(
            json_valid=True,
            tool_correct=False,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="wrong_tool",
        )

    # ---------------------------------------------------------
    # 4. Schema validity
    # ---------------------------------------------------------

    try:
        validate(
            instance=arguments,
            schema=tool_schema["parameters"],
        )

        schema_valid = True

    except ValidationError:
        schema_valid = False

    if not schema_valid:
        return EvaluationResult(
            json_valid=True,
            tool_correct=True,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="schema_invalid",
        )

    # ---------------------------------------------------------
    # 5. Task correctness
    # ---------------------------------------------------------

    arguments_correct = arguments == expected_arguments

    if not arguments_correct:
        return EvaluationResult(
            json_valid=True,
            tool_correct=True,
            schema_valid=True,
            arguments_correct=False,
            task_success=False,
            failure_type="arguments_incorrect",
        )

    # ---------------------------------------------------------
    # 6. Complete success
    # ---------------------------------------------------------

    return EvaluationResult(
        json_valid=True,
        tool_correct=True,
        schema_valid=True,
        arguments_correct=True,
        task_success=True,
        failure_type=None,
    )