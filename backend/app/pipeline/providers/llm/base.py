from abc import ABC, abstractmethod
from typing import Any

class BaseLlmProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        pass
