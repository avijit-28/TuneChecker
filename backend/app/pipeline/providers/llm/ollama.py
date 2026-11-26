import json
import re
import httpx
from typing import Any
from app.config import settings
from app.pipeline.providers.llm.base import BaseLlmProvider
from app.utils.errors import AppError

class OllamaLlmProvider(BaseLlmProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or settings.OLLAMA_BASE_URL
        self.model = model or settings.LLM_MODEL
        self.endpoint = f"{self.base_url.rstrip('/')}/api/chat"

    def _try_gemini_fallback(self, system_prompt: str, user_prompt: str):
        if getattr(settings, "LLM_FALLBACK_PROVIDER", None) == "gemini" and getattr(settings, "GEMINI_API_KEY", None):
            try:
                from app.pipeline.providers.llm.gemini import GeminiLlmProvider
                return GeminiLlmProvider().generate_json(system_prompt, user_prompt)
            except Exception:
                return None
        return None

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json",
            "options": {
                "temperature": settings.LLM_TEMPERATURE,
                "seed": 42,
                "num_predict": 2048
            },
            "stream": False
        }

        try:
            response = httpx.post(self.endpoint, json=payload, timeout=settings.LLM_TIMEOUT_SEC)
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            fallback = self._try_gemini_fallback(system_prompt, user_prompt)
            if fallback is not None:
                return fallback
            if isinstance(e, httpx.TimeoutException):
                raise AppError("LLM_TIMEOUT", f"Ollama generation timed out after {settings.LLM_TIMEOUT_SEC}s.", 504, retryable=True)
            raise AppError("LLM_UNAVAILABLE", f"Failed to communicate with Ollama: {str(e)}", 503, retryable=True)

        if response.status_code != 200:
            fallback = self._try_gemini_fallback(system_prompt, user_prompt)
            if fallback is not None:
                return fallback
            raise AppError("LLM_UNAVAILABLE", f"Ollama returned HTTP {response.status_code}: {response.text}", 503, retryable=True)

        try:
            res_data = response.json()
            content = res_data.get("message", {}).get("content", "").strip()

            # Strip markdown ```json fences if present
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Attempt graceful JSON truncation recovery (e.g. cut off inside an array or string)
                # Find last valid object or array boundary
                trimmed = content
                for cutoff in range(len(content) - 1, max(0, len(content) - 200), -1):
                    sub = content[:cutoff].strip()
                    if sub.endswith("}"):
                        for closer in ["]}", "}"]:
                            try:
                                return json.loads(sub + closer)
                            except Exception:
                                pass
                raise
        except Exception as e:
            raise AppError("LLM_INVALID_OUTPUT", f"Failed to parse LLM response as JSON: {str(e)}", 500, retryable=True)
