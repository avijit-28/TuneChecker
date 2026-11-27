import json
import logging
import re
from typing import Any
from app.config import settings
from app.pipeline.providers.llm.base import BaseLlmProvider
from app.utils.errors import AppError

logger = logging.getLogger("tune_checker.llm.gemini")

class GeminiLlmProvider(BaseLlmProvider):
    """Google Gemini LLM provider for zero-failure fallback and cloud reasoning."""

    def __init__(self, api_key: str = None, model: str = "gemini-3.8-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise AppError("CONFIG_ERROR", "GEMINI_API_KEY is not configured.", 500)
        self.model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        from google import genai
        from google.genai import types

        client = genai.Client(
            api_key=self.api_key,
            http_options=types.HttpOptions(
                timeout=20000,
                retry_options=types.HttpRetryOptions(attempts=1),
            ),
        )
        combined_prompt = (
            f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n"
            f"USER REQUEST:\n{user_prompt}\n\n"
            "Return valid JSON only without markdown code blocks."
        )

        try:
            resp = client.models.generate_content(
                model=self.model,
                contents=combined_prompt,
            )
            content = (getattr(resp, "text", None) or "").strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            return json.loads(content)
        except Exception as e:
            logger.warning(f"Gemini fallback generation error: {e}")
            raise AppError("LLM_UNAVAILABLE", f"Gemini error: {str(e)}", 503, retryable=True)
