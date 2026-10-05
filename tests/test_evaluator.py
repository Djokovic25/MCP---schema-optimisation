from src.schemas.loader import load_schema
from src.evaluation.evaluator import evaluate_response


SCHEMA_PATH = "schemas/synthetic/zentrax_lookup.json"


def get_schema():
    return load_schema(SCHEMA_PATH)
def test_correct_invocation():

    response = """
    {
        "tool": "zentrax_lookup",
        "arguments": {
            "query": "authentication failures",
            "mode": "m7"
        }
    }
    """

    result = evaluate_response(
        raw_response=response,
        tool_schema=get_schema(),
        expected_arguments={
            "query": "authentication failures",
            "mode": "m7"
        },
        expected_tool="zentrax_lookup",
    )

    assert result.json_valid
    assert result.tool_correct
    assert result.schema_valid
    assert result.arguments_correct
    assert result.task_success
    assert result.failure_type is None

def test_invalid_json():

    response = """
    {"tool": "zentrax_lookup",
    """

    result = evaluate_response(
        raw_response=response,
        tool_schema=get_schema(),
        expected_arguments={
            "query": "authentication failures",
            "mode": "m7"
        },
        expected_tool="zentrax_lookup",
    )

    assert not result.json_valid
    assert not result.task_success
    assert result.failure_type == "invalid_json"

def test_wrong_tool():

    response = """
    {
        "tool": "other_tool",
        "arguments": {
            "query": "authentication failures",
            "mode": "m7"
        }
    }
    """

    result = evaluate_response(
        raw_response=response,
        tool_schema=get_schema(),
        expected_arguments={
            "query": "authentication failures",
            "mode": "m7"
        },
        expected_tool="zentrax_lookup",
    )

    assert result.json_valid
    assert not result.tool_correct
    assert not result.task_success
    assert result.failure_type == "wrong_tool"
def test_schema_invalid():

    response = """
    {
        "tool": "zentrax_lookup",
        "arguments": {
            "query": "authentication failures",
            "mode": "M7"
        }
    }
    """

    result = evaluate_response(
        raw_response=response,
        tool_schema=get_schema(),
        expected_arguments={
            "query": "authentication failures",
            "mode": "m7"
        },
        expected_tool="zentrax_lookup",
    )

    assert result.json_valid
    assert result.tool_correct
    assert not result.schema_valid
    assert not result.task_success
    assert result.failure_type == "schema_invalid"
def test_arguments_incorrect():

    response = """
    {
        "tool": "zentrax_lookup",
        "arguments": {
            "query": "authentication failures",
            "mode": "m7",
            "limit": 100
        }
    }
    """

    result = evaluate_response(
        raw_response=response,
        tool_schema=get_schema(),
        expected_arguments={
            "query": "authentication failures",
            "mode": "m7",
            "limit": 20
        },
        expected_tool="zentrax_lookup",
    )

    assert result.json_valid
    assert result.tool_correct
    assert result.schema_valid
    assert not result.arguments_correct
    assert not result.task_success
    assert result.failure_type == "arguments_incorrect"