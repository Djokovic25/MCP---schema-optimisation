# import os

# from dotenv import load_dotenv

# from src.llm.gemini import GeminiClient


# def main():

#     load_dotenv()

#     model_name = os.getenv("GEMINI_MODEL")

#     if not model_name:
#         raise ValueError(
#             "GEMINI_MODEL was not found in the environment."
#         )

#     client = GeminiClient(
#         model=model_name,
#     )

#     prompt = """Return ONLY this JSON object:

# {
#   "status": "ok"
# }
# """

#     response = client.generate(prompt)

#     print("MODEL:", model_name)
#     print()
#     print("RESPONSE:")
#     print(response.raw_text)
#     print()
#     print("INPUT TOKENS:", response.input_tokens)
#     print("OUTPUT TOKENS:", response.output_tokens)
#     print("LATENCY (ms):", response.latency_ms)


# if __name__ == "__main__":
#     main()
import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise RuntimeError("GROQ_API_KEY was not found in .env")

client = Groq(api_key=api_key)
models = client.models.list()

for model in models.data:
    if model.id == "qwen/qwen3.8-27b":
        print("Model available:", model.id)
        break
else:
    print("Model not listed for this API key.")