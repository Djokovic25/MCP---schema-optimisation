import os
import time
from typing import Any, Dict

from google import genai
from google.genai import types

from .base import LLMClient, LLMResponse


class GeminiClient(LLMClient):

    def __init__(self, model: str):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY was not found in the environment."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        tool_schema: Dict[str, Any],
    ) -> LLMResponse:

        start_time = time.perf_counter()

        function_declaration = types.FunctionDeclaration(
            name=tool_schema["name"],
            description=tool_schema.get("description"),
            parameters_json_schema=tool_schema["parameters"],
        )

        tool = types.Tool(
            function_declarations=[function_declaration]
        )

        config = types.GenerateContentConfig(
            tools=[tool],

            automatic_function_calling=(
                types.AutomaticFunctionCallingConfig(
                    disable=True
                )
            ),

            tool_config=types.ToolConfig(
                function_calling_config=(
                    types.FunctionCallingConfig(
                        mode="ANY",
                        allowed_function_names=[
                            tool_schema["name"]
                        ],
                    )
                )
            ),
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=config,
        )

        latency_ms = (
            time.perf_counter() - start_time
        ) * 1000

        usage = getattr(
            response,
            "usage_metadata",
            None,
        )

        input_tokens = None
        output_tokens = None

        if usage:
            input_tokens = getattr(
                usage,
                "prompt_token_count",
                None,
            )

            output_tokens = getattr(
                usage,
                "candidates_token_count",
                None,
            )

        function_calls = response.function_calls

        if not function_calls:
            raise RuntimeError(
                "Gemini did not return a function call."
            )

        function_call = function_calls[0]

        return LLMResponse(
            raw_text=None,
            function_name=function_call.name,
            arguments=dict(function_call.args),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )