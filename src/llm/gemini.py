import os
import time

from dotenv import load_dotenv
from google import genai

from .base import LLMClient, LLMResponse


class GeminiClient(LLMClient):

    def __init__(
        self,
        model: str,
    ):
       # load_dotenv()

        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY was not found in the environment."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str) -> LLMResponse:

        start_time = time.perf_counter()

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000

        usage = getattr(response, "usage_metadata", None)

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

        return LLMResponse(
            raw_text=response.text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
        )