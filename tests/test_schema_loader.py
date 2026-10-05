from src.schemas.loader import load_schema


def test_load_zentrax_schema():

    schema = load_schema(
        "schemas/synthetic/zentrax_lookup.json"
    )

    assert schema["name"] == "zentrax_lookup"

    assert "query" in schema["parameters"]["properties"]
    assert "mode" in schema["parameters"]["properties"]
    assert "limit" in schema["parameters"]["properties"]
    assert "include_meta" in schema["parameters"]["properties"]

    assert schema["parameters"]["required"] == [
        "query",
        "mode",
    ]