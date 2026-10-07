from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from jsonschema import ValidationError, validate


@dataclass
class EvaluationResult:
    tool_correct: bool
    schema_valid: bool
    arguments_correct: bool
    task_success: bool
    failure_type: Optional[str]


def evaluate_response(
    function_name: Optional[str],
    arguments: Optional[Dict[str, Any]],
    tool_schema: Dict[str, Any],
    expected_arguments: Dict[str, Any],
    expected_tool: str,
    acceptable_arguments: Optional[List[Dict[str, Any]]] = None,
) -> EvaluationResult:

    # ---------------------------------------------------------
    # 1. Check whether the model returned a function call
    # ---------------------------------------------------------
    if function_name is None:
        return EvaluationResult(
            tool_correct=False,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="no_function_call",
        )

    # ---------------------------------------------------------
    # 2. Check whether the correct tool was selected
    # ---------------------------------------------------------
    tool_correct = function_name == expected_tool

    if not tool_correct:
        return EvaluationResult(
            tool_correct=False,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="wrong_tool",
        )

    # ---------------------------------------------------------
    # 3. Check argument structure
    # ---------------------------------------------------------
    if not isinstance(arguments, dict):
        return EvaluationResult(
            tool_correct=True,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="invalid_arguments_structure",
        )

    # ---------------------------------------------------------
    # 4. Validate arguments against the FULL ground-truth
    #    schema, not the ablated schema.
    #
    #    This is important:
    #    schema ablation controls what the model sees.
    #    Evaluation should always use the original schema.
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
            tool_correct=True,
            schema_valid=False,
            arguments_correct=False,
            task_success=False,
            failure_type="schema_invalid",
        )

    # ---------------------------------------------------------
    # 5. Check semantic argument correctness
    #
    #    Most tasks use exact expected_arguments.
    #
    #    A task may optionally provide acceptable_arguments when
    #    more than one representation is explicitly considered
    #    valid by the benchmark.
    # ---------------------------------------------------------
    if acceptable_arguments:
        arguments_correct = (
            arguments in acceptable_arguments
        )
    else:
        arguments_correct = (
            arguments == expected_arguments
        )

    if not arguments_correct:
        return EvaluationResult(
            tool_correct=True,
            schema_valid=True,
            arguments_correct=False,
            task_success=False,
            failure_type="arguments_incorrect",
        )

    # ---------------------------------------------------------
    # 6. Everything passed
    # ---------------------------------------------------------
    return EvaluationResult(
        tool_correct=True,
        schema_valid=True,
        arguments_correct=True,
        task_success=True,
        failure_type=None,
    )