import json
from typing import Dict, Any


def build_tool_invocation_prompt(
    task_description: str,
    disclosed_schema: Dict[str, Any],
) -> str:
    """
    Build the prompt used to ask the model to construct
    a tool invocation.
    """

    schema_text = json.dumps(
        disclosed_schema,
        indent=2,
    )

    return f"""You are given a task and information about a tool.

Your job is to construct the tool invocation that best satisfies the task.

TASK:
{task_description}

TOOL INFORMATION:
{schema_text}

Return ONLY a JSON object in exactly this format:

{{
  "tool": "tool_name",
  "arguments": {{
    "parameter_name": "value"
  }}
}}

Do not include markdown.
Do not include explanations.
Do not invent parameters that are not present in the tool information.
"""