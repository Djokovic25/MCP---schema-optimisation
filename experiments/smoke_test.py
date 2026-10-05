import os

from dotenv import load_dotenv

from src.llm.gemini import GeminiClient


def main():

    load_dotenv()

    model_name = os.getenv("GEMINI_MODEL")

    if not model_name:
        raise ValueError(
            "GEMINI_MODEL was not found in the environment."
        )

    client = GeminiClient(
        model=model_name,
    )

    prompt = """Return ONLY this JSON object:

{
  "status": "ok"
}
"""

    response = client.generate(prompt)

    print("MODEL:", model_name)
    print()
    print("RESPONSE:")
    print(response.raw_text)
    print()
    print("INPUT TOKENS:", response.input_tokens)
    print("OUTPUT TOKENS:", response.output_tokens)
    print("LATENCY (ms):", response.latency_ms)


if __name__ == "__main__":
    main()