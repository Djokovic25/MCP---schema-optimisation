from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LLMResponse:
    raw_text: Optional[str] = None
    function_name: Optional[str] = None
    arguments: Optional[Dict[str, Any]] = None

    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None


class LLMClient(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        tool_schema: Dict[str, Any],
    ) -> LLMResponse:
        """Generate a native tool call from the model."""
        raise NotImplementedError