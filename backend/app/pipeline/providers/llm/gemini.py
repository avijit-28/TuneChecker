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

    def __init__(self, api_key: str = None, model: str = "gemini-3.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        if not self.api_key:
            raise AppError("CONFIG_ERROR", "GEMINI_API_KEY is not configured.", 500)
        self.model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        from google import genai

        client = genai.Client(api_key=self.api_key)
        combined_prompt = (
            f"SYSTEM INSTRUCTIONS:\n{system_prompt}\n\n"
            f"USER REQUEST:\n{user_prompt}\n\n"
            "Return valid JSON only without markdown code blocks."
        )

        try:
            interaction = client.interactions.create(
                model=self.model,
                input=combined_prompt,
                store=False,
            )
            content = getattr(interaction, "output_text", "")
            if not content:
                for step in getattr(interaction, "steps", None) or []:
                    if getattr(step, "type", None) in (None, "model_output"):
                        for item in getattr(step, "content", None) or []:
                            t = getattr(item, "text", "")
                            if t:
                                content += t
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\s*", "", content)
                content = re.sub(r"\s*```$", "", content)

            return json.loads(content)
        except Exception as e:
            logger.warning(f"Gemini fallback generation error: {e}")
            raise AppError("LLM_UNAVAILABLE", f"Gemini error: {str(e)}", 503, retryable=True)
