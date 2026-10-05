from src.schemas.loader import load_schema
from src.schemas.disclosure import build_disclosure
from src.llm.prompts import build_tool_invocation_prompt


SCHEMA_PATH = "schemas/synthetic/zentrax_lookup.json"


def test_prompt_contains_task_and_tool():

    schema = load_schema(SCHEMA_PATH)

    disclosed = build_disclosure(
        schema,
        "name",
    )

    prompt = build_tool_invocation_prompt(
        task_description=(
            "Search for records about authentication failures "
            "using retrieval mode m7."
        ),
        disclosed_schema=disclosed,
    )

    assert "authentication failures" in prompt
    assert "zentrax_lookup" in prompt
    assert '"name": "zentrax_lookup"' in prompt


def test_name_condition_does_not_leak_full_schema():

    schema = load_schema(SCHEMA_PATH)

    disclosed = build_disclosure(
        schema,
        "name",
    )

    prompt = build_tool_invocation_prompt(
        task_description="Search for authentication failures.",
        disclosed_schema=disclosed,
    )

    assert "query" not in prompt
    assert "include_meta" not in prompt
    assert "m7" not in prompt