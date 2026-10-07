import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.schemas.loader import load_schema


load_dotenv()

schema = load_schema(
    "schemas/synthetic/search_issues.json"
)

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

function_declaration = types.FunctionDeclaration(
    name=schema["name"],
    description=schema.get("description"),
    parameters_json_schema=schema["parameters"],
)

tool = types.Tool(
    function_declarations=[function_declaration]
)

config = types.GenerateContentConfig(
    tools=[tool],

    automatic_function_calling=types.AutomaticFunctionCallingConfig(
        disable=True
    ),

    tool_config=types.ToolConfig(
        function_calling_config=types.FunctionCallingConfig(
            mode="ANY",
            allowed_function_names=[
                schema["name"]
            ],
        )
    ),
)

response = client.models.generate_content(
    model="gemini-3.1-flash-lite",
    contents=(
        "Find AUTH_FAILURES issues that are currently open."
    ),
    config=config,
)

print("=" * 60)
print("NATIVE FUNCTION CALL TEST")
print("=" * 60)

print("\nFunction calls:")

for function_call in response.function_calls:
    print("Function name:", function_call.name)
    print("Arguments:", function_call.args)

print("\nUsage:")
print("Input tokens:", response.usage_metadata.prompt_token_count)
print("Output tokens:", response.usage_metadata.candidates_token_count)

print("\nRaw function calls object:")
print(response.function_calls)