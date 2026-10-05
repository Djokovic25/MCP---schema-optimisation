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