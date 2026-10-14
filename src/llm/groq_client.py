
import json
import os
import time
from typing import Any, Dict

from groq import Groq

from .base import LLMClient, LLMResponse


class GroqClient(LLMClient):
    def __init__(self, model: str):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY was not found in the environment."
            )

        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        tool_schema: Dict[str, Any],
    ) -> LLMResponse:
        function_definition = {
            "type": "function",
            "function": {
                "name": tool_schema["name"],
                "description": tool_schema.get("description") or "",
                "parameters": tool_schema["parameters"],
            },
        }

        start_time = time.perf_counter()

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt},
            ],
            tools=[function_definition],
            tool_choice={
                "type": "function",
                "function": {"name": tool_schema["name"]},
            },
            parallel_tool_calls=False,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        choice = response.choices[0]
        message = choice.message
        usage = response.usage

        input_tokens = (
            getattr(usage, "prompt_tokens", None)
            if usage else None
        )
        output_tokens = (
            getattr(usage, "completion_tokens", None)
            if usage else None
        )

        tool_calls = message.tool_calls or []

        if not tool_calls:
            return LLMResponse(
                raw_text=message.content,
                function_name=None,
                arguments=None,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
            )

        # We request a single named tool and disable parallel calls.
        # If the API nevertheless returns multiple calls, do not silently
        # treat the first as the complete response.
        if len(tool_calls) != 1:
            raise RuntimeError(
                f"Expected one tool call; received {len(tool_calls)}."
            )

        function_call = tool_calls[0].function

        try:
            arguments = json.loads(function_call.arguments)
        except (json.JSONDecodeError, TypeError):
            arguments = None

        return LLMResponse(
            raw_text=message.content,
            function_name=function_call.name,
            arguments=arguments if isinstance(arguments, dict) else None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )
