from src.llm.base import LLMResponse
from src.llm.gemini import GeminiClient


def test_response_structure():
    response = LLMResponse(
        raw_text="{}",
        input_tokens=10,
        output_tokens=5,
        latency_ms=100.0,
    )

    assert response.raw_text == "{}"
    assert response.input_tokens == 10
    assert response.output_tokens == 5


def test_gemini_client_requires_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    try:
        GeminiClient(model="test-model")
        assert False, "Expected missing API key error"
    except ValueError:
        pass