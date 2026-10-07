# from dataclasses import dataclass
# from typing import Any, Dict, Optional

# from src.evaluation.evaluator import evaluate_response
# from src.llm.base import LLMClient


# @dataclass
# class TrialResult:
#     experiment: str
#     task_id: str
#     condition: str
#     model: str
#     repetition: int

#     function_name: Optional[str]
#     arguments: Optional[Dict[str, Any]]

#     tool_correct: bool
#     schema_valid: bool
#     arguments_correct: bool
#     task_success: bool
#     failure_type: Optional[str]

#     input_tokens: Optional[int]
#     output_tokens: Optional[int]
#     latency_ms: Optional[float]


# def run_trial(
#     experiment: str,
#     task: Dict[str, Any],
#     tool_schema: Dict[str, Any],
#     disclosed_schema: Dict[str, Any],
#     condition: str,
#     client: LLMClient,
#     model_name: str,
#     repetition: int,
# ) -> TrialResult:

#     response = client.generate(
#         prompt=task["description"],
#         tool_schema=disclosed_schema,
#     )

#     evaluation = evaluate_response(
#         function_name=response.function_name,
#         arguments=response.arguments,
#         tool_schema=tool_schema,
#         expected_arguments=task["expected_arguments"],
#         expected_tool=tool_schema["name"],
#     )

#     return TrialResult(
#         experiment=experiment,
#         task_id=task["id"],
#         condition=condition,
#         model=model_name,
#         repetition=repetition,

#         function_name=response.function_name,
#         arguments=response.arguments,

#         tool_correct=evaluation.tool_correct,
#         schema_valid=evaluation.schema_valid,
#         arguments_correct=evaluation.arguments_correct,
#         task_success=evaluation.task_success,
#         failure_type=evaluation.failure_type,

#         input_tokens=response.input_tokens,
#         output_tokens=response.output_tokens,
#         latency_ms=response.latency_ms,
#     )

#continuing from 17
from dataclasses import dataclass
from typing import Any, Dict, Optional

from src.evaluation.evaluator import evaluate_response
from src.llm.base import LLMClient


@dataclass
class TrialResult:
    experiment: str
    task_id: str
    condition: str
    model: str
    repetition: int

    function_name: Optional[str]
    arguments: Optional[Dict[str, Any]]

    tool_correct: bool
    schema_valid: bool
    arguments_correct: bool
    task_success: bool
    failure_type: Optional[str]

    input_tokens: Optional[int]
    output_tokens: Optional[int]
    latency_ms: Optional[float]


def run_trial(
    experiment: str,
    task: Dict[str, Any],
    tool_schema: Dict[str, Any],
    disclosed_schema: Dict[str, Any],
    condition: str,
    client: LLMClient,
    model_name: str,
    repetition: int,
) -> TrialResult:

    response = client.generate(
        prompt=task["description"],
        tool_schema=disclosed_schema,
    )

    evaluation = evaluate_response(
        function_name=response.function_name,
        arguments=response.arguments,
        tool_schema=tool_schema,
        expected_arguments=task["expected_arguments"],
        expected_tool=tool_schema["name"],
        acceptable_arguments=task.get("acceptable_arguments"),
    )

    return TrialResult(
        experiment=experiment,
        task_id=task["id"],
        condition=condition,
        model=model_name,
        repetition=repetition,

        function_name=response.function_name,
        arguments=response.arguments,

        tool_correct=evaluation.tool_correct,
        schema_valid=evaluation.schema_valid,
        arguments_correct=evaluation.arguments_correct,
        task_success=evaluation.task_success,
        failure_type=evaluation.failure_type,

        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        latency_ms=response.latency_ms,
    )