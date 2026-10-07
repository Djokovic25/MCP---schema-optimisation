from src.evaluation.evaluator import evaluate_response


TOOL_SCHEMA = {
    "name": "search_issues",
    "description": "Search issues using text, status, and result-count filters.",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Text to search for in issue titles and descriptions.",
            },
            "status": {
                "type": "string",
                "description": "Filter issues by their current workflow status.",
                "enum": ["open", "in_progress", "closed"],
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of issues to return.",
                "minimum": 1,
                "maximum": 100,
            },
            "include_comments": {
                "type": "boolean",
                "description": "Whether issue comments should be included in the results.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


EXPECTED_TOOL = "search_issues"


def test_correct_function_call():
    result = evaluate_response(
        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES",
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is True
    assert result.arguments_correct is True
    assert result.task_success is True
    assert result.failure_type is None


def test_no_function_call():
    result = evaluate_response(
        function_name=None,
        arguments=None,
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is False
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "no_function_call"


def test_wrong_tool():
    result = evaluate_response(
        function_name="other_tool",
        arguments={
            "query": "AUTH_FAILURES",
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is False
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "wrong_tool"


def test_invalid_arguments_structure():
    result = evaluate_response(
        function_name="search_issues",
        arguments=None,
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "invalid_arguments_structure"


def test_schema_invalid_missing_required_parameter():
    result = evaluate_response(
        function_name="search_issues",
        arguments={},
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "schema_invalid"


def test_schema_invalid_wrong_type():
    result = evaluate_response(
        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES",
            "max_results": "twenty",
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
            "max_results": 20,
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "schema_invalid"


def test_schema_invalid_enum_value():
    result = evaluate_response(
        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES",
            "status": "pending",
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
            "status": "open",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is False
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "schema_invalid"


def test_arguments_incorrect_but_schema_valid():
    result = evaluate_response(
        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES",
            "status": "closed",
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
            "status": "open",
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is True
    assert result.arguments_correct is False
    assert result.task_success is False
    assert result.failure_type == "arguments_incorrect"


def test_correct_multiple_arguments():
    result = evaluate_response(
        function_name="search_issues",
        arguments={
            "query": "AUTH_FAILURES",
            "status": "closed",
            "max_results": 20,
            "include_comments": True,
        },
        tool_schema=TOOL_SCHEMA,
        expected_arguments={
            "query": "AUTH_FAILURES",
            "status": "closed",
            "max_results": 20,
            "include_comments": True,
        },
        expected_tool=EXPECTED_TOOL,
    )

    assert result.tool_correct is True
    assert result.schema_valid is True
    assert result.arguments_correct is True
    assert result.task_success is True
    assert result.failure_type is None