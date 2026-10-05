from typing import Dict, Any


def build_disclosure(
    schema: Dict[str, Any],
    condition: str,
) -> Dict[str, Any]:
    """
    Build the schema representation exposed to the LLM.

    Conditions:
        name       -> tool name only
        parameters -> tool name + parameter names/types
        full       -> complete tool schema
    """

    if condition == "name":
        return {
            "name": schema["name"]
        }

    if condition == "parameters":
        properties = schema["parameters"]["properties"]

        parameter_summary = {}

        for name, details in properties.items():
            parameter_summary[name] = {
                "type": details["type"]
            }

        return {
            "name": schema["name"],
            "parameters": parameter_summary
        }

    if condition == "full":
        return schema

    raise ValueError(
        f"Unknown disclosure condition: {condition}"
    )