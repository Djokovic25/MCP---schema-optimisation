from src.experiments.runner import TrialResult


def test_trial_result_creation():

    result = TrialResult(
        experiment="schema_ablation_v1",
        task_id="T1",
        condition="full",
        model="gemini-3.1-flash-lite",
        repetition=1,

        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES"
        },

        tool_correct=True,
        schema_valid=True,
        arguments_correct=True,
        task_success=True,
        failure_type=None,

        input_tokens=174,
        output_tokens=19,
        latency_ms=4786.12,
    )

    assert result.experiment == "schema_ablation_v1"
    assert result.task_id == "T1"
    assert result.condition == "full"
    assert result.model == "gemini-3.1-flash-lite"
    assert result.repetition == 1

    assert result.function_name == "search_issues"
    assert result.arguments == {
        "query": "AUTH_FAILURES"
    }

    assert result.tool_correct is True
    assert result.schema_valid is True
    assert result.arguments_correct is True
    assert result.task_success is True
    assert result.failure_type is None

    assert result.input_tokens == 174
    assert result.output_tokens == 19
    assert result.latency_ms == 4786.12