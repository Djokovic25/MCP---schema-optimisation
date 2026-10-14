
import json
import os
from pathlib import Path

from dotenv import load_dotenv

from src.llm.groq_client import GroqClient
from src.schemas.loader import load_schema

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

MODEL = "openai/gpt-oss-20b"
SCHEMA_PATH = (
    PROJECT_ROOT / "schemas/synthetic/search_issues_v2.json"
)

schema = load_schema(SCHEMA_PATH)
client = GroqClient(model=MODEL)

response = client.generate(
    prompt="Find issues with the exact error code AUTH_FAILURES.",
    tool_schema=schema,
)

print(json.dumps({
    "model": MODEL,
    "function_name": response.function_name,
    "arguments": response.arguments,
    "input_tokens": response.input_tokens,
    "output_tokens": response.output_tokens,
    "latency_ms": response.latency_ms,
}, indent=2))
