from src.schemas.loader import load_schema
from src.schemas.disclosure import build_disclosure
from src.schemas.disclosure import build_task_disclosure

SCHEMA_PATH = "schemas/synthetic/zentrax_lookup.json"


def test_name_disclosure():

    schema = load_schema(SCHEMA_PATH)

    disclosed = build_disclosure(schema, "name")

    assert disclosed == {
        "name": "zentrax_lookup"
    }


def test_parameters_disclosure():

    schema = load_schema(SCHEMA_PATH)

    disclosed = build_disclosure(schema, "parameters")

    assert disclosed["name"] == "zentrax_lookup"

    assert disclosed["parameters"]["query"]["type"] == "string"
    assert disclosed["parameters"]["mode"]["type"] == "string"
    assert disclosed["parameters"]["limit"]["type"] == "integer"
    assert disclosed["parameters"]["include_meta"]["type"] == "boolean"

    # These should NOT be exposed in this condition.
    assert "description" not in disclosed
    assert "required" not in disclosed["parameters"]


def test_full_disclosure():

    schema = load_schema(SCHEMA_PATH)

    disclosed = build_disclosure(schema, "full")

    assert disclosed == schema


def test_invalid_condition():

    schema = load_schema(SCHEMA_PATH)

    try:
        build_disclosure(schema, "invalid")
        assert False, "Expected ValueError"
    except ValueError:
        pass

from src.schemas.disclosure import build_ablation


def test_remove_tool_description():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                }
            }
        }
    }

    result = build_ablation(
        schema,
        ["tool_description"],
    )

    assert "description" not in result
    assert result["name"] == "test_tool"
    assert "description" in result["parameters"]["properties"]["query"]


def test_remove_parameter_description():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                }
            }
        }
    }

    result = build_ablation(
        schema,
        ["parameter_description"],
    )

    parameter = result["parameters"]["properties"]["query"]

    assert "description" not in parameter
    assert parameter["type"] == "string"


def test_remove_type():

    schema = {
        "name": "test_tool",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            }
        }
    }

    result = build_ablation(
        schema,
        ["type"],
    )

    assert "type" not in result["parameters"]["properties"]["query"]


def test_remove_enum():

    schema = {
        "name": "test_tool",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "closed"]
                }
            }
        }
    }

    result = build_ablation(
        schema,
        ["enum"],
    )

    parameter = result["parameters"]["properties"]["status"]

    assert "enum" not in parameter
    assert parameter["type"] == "string"


def test_remove_constraints():

    schema = {
        "name": "test_tool",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100
                }
            }
        }
    }

    result = build_ablation(
        schema,
        ["constraints"],
    )

    parameter = result["parameters"]["properties"]["limit"]

    assert parameter["type"] == "integer"
    assert "minimum" not in parameter
    assert "maximum" not in parameter


def test_remove_required():

    schema = {
        "name": "test_tool",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            },
            "required": ["query"]
        }
    }

    result = build_ablation(
        schema,
        ["required"],
    )

    assert "required" not in result["parameters"]


def test_ablation_does_not_modify_original():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                }
            }
        }
    }

    build_ablation(
        schema,
        ["tool_description", "parameter_description", "type"],
    )

    assert schema["description"] == "Tool description"
    assert schema["parameters"]["properties"]["query"]["type"] == "string"
    assert "description" in schema["parameters"]["properties"]["query"]

def test_task_disclosure_keeps_only_relevant_parameters():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results"
                },
                "state": {
                    "type": "string",
                    "description": "Issue state"
                }
            },
            "required": ["query"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["query"]
    )

    properties = result["parameters"]["properties"]

    assert list(properties.keys()) == ["query"]

    assert properties["query"]["type"] == "string"
    assert properties["query"]["description"] == "Query text"

    assert "limit" not in properties
    assert "state" not in properties


def test_task_disclosure_keeps_relevant_metadata():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text",
                    "enum": ["A", "B"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "minimum": 1,
                    "maximum": 100
                }
            },
            "required": ["query"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["query"]
    )

    parameter = (
        result["parameters"]["properties"]["query"]
    )

    assert parameter["type"] == "string"
    assert parameter["description"] == "Query text"
    assert parameter["enum"] == ["A", "B"]


def test_task_disclosure_updates_required():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                },
                "limit": {
                    "type": "integer"
                }
            },
            "required": ["query", "limit"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["query"]
    )

    assert result["parameters"]["required"] == ["query"]


def test_task_disclosure_does_not_modify_original():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                }
            },
            "required": ["query", "limit"]
        }
    }

    build_task_disclosure(
        schema,
        ["query"]
    )

    # Original schema must remain unchanged.
    assert "limit" in schema["parameters"]["properties"]

    assert (
        schema["parameters"]["required"]
        == ["query", "limit"]
    )

    assert (
        schema["parameters"]["properties"]["limit"]["description"]
        == "Maximum results"
    )
def test_task_disclosure_adds_one_irrelevant_parameter():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results"
                },
                "state": {
                    "type": "string",
                    "description": "Issue state"
                }
            },
            "required": ["query"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["query"],
        condition="relevant_plus_one_irrelevant",
        irrelevant_parameter="limit",
    )

    properties = result["parameters"]["properties"]

    assert list(properties.keys()) == [
        "query",
        "limit",
    ]

    assert properties["query"]["type"] == "string"
    assert properties["limit"]["type"] == "integer"

    assert "state" not in properties


def test_minimal_relevant_removes_descriptions_and_constraints():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Query text",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results",
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["query", "limit"],
        condition="minimal_relevant",
    )

    assert "description" not in result

    query = result["parameters"]["properties"]["query"]
    limit = result["parameters"]["properties"]["limit"]

    assert query["type"] == "string"
    assert "description" not in query

    assert limit["type"] == "integer"
    assert "description" not in limit
    assert "minimum" not in limit
    assert "maximum" not in limit


def test_minimal_relevant_preserves_enum_and_array_structure():

    schema = {
        "name": "test_tool",
        "description": "Tool description",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "description": "Issue state",
                    "enum": ["open", "closed"],
                },
                "labels": {
                    "type": "array",
                    "description": "Issue labels",
                    "items": {
                        "type": "string"
                    },
                },
            },
            "required": ["state"]
        }
    }

    result = build_task_disclosure(
        schema,
        ["state", "labels"],
        condition="minimal_relevant",
    )

    state = result["parameters"]["properties"]["state"]
    labels = result["parameters"]["properties"]["labels"]

    assert state["type"] == "string"
    assert state["enum"] == ["open", "closed"]
    assert "description" not in state

    assert labels["type"] == "array"
    assert labels["items"]["type"] == "string"
    assert "description" not in labels


def test_task_disclosure_invalid_condition():

    schema = {
        "name": "test_tool",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string"
                }
            }
        }
    }

    try:
        build_task_disclosure(
            schema,
            ["query"],
            condition="invalid",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass