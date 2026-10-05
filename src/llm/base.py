from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    raw_text: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None


class LLMClient(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
    ) -> LLMResponse:
        """Generate a response from the model."""
        raise NotImplementedError