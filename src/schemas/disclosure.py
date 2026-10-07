from copy import deepcopy
from typing import Dict, Any, List


def build_disclosure(
    schema: Dict[str, Any],
    condition: str,
) -> Dict[str, Any]:

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
        return deepcopy(schema)

    raise ValueError(
        f"Unknown disclosure condition: {condition}"
    )


def build_ablation(
    schema: Dict[str, Any],
    removed_components: List[str],
) -> Dict[str, Any]:

    disclosed_schema = deepcopy(schema)

    if "tool_description" in removed_components:
        disclosed_schema.pop("description", None)

    properties = disclosed_schema["parameters"]["properties"]

    for parameter in properties.values():

        if "parameter_description" in removed_components:
            parameter.pop("description", None)

        if "type" in removed_components:
            parameter.pop("type", None)

            # Remove nested type information as well.
            # Example:
            # "labels": {
            #     "type": "array",
            #     "items": {"type": "string"}
            # }
            if isinstance(parameter.get("items"), dict):
                parameter["items"].pop("type", None)

        if "enum" in removed_components:
            parameter.pop("enum", None)

        if "constraints" in removed_components:
            parameter.pop("minimum", None)
            parameter.pop("maximum", None)

    if "required" in removed_components:
        disclosed_schema["parameters"].pop("required", None)

    return disclosed_schema