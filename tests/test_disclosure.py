from src.schemas.loader import load_schema
from src.schemas.disclosure import build_disclosure


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