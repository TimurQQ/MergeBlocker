"""Code analyzer using LLM for PR review."""

import json
import logging
from typing import Any, Dict, List

from src.analysis.prompts import ReviewPrompts
from src.clients.llm_client import LLMClient
from src.config import Config
from src.utils.async_retry import async_retry_on_invalid_json

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyzes code changes using LLM (OpenRouter-compatible API)."""

    def __init__(self):
        self.client = LLMClient()
        self.fallback_client = None  # Lazy init для fallback модели

    def _estimate_prompt_tokens(self, prompt: str) -> int:
        """
        Оценивает количество токенов в промпте.

        Простая эвристика: 1 токен ≈ 4 символа
        """
        return len(prompt) // 4

    def _get_client_for_prompt(self, prompt: str) -> LLMClient:
        """
        Выбирает клиент в зависимости от размера промпта.

        Если промпт слишком большой (> fallback_threshold), использует fallback модель
        с большим контекстом (Gemini 3 Pro - 1M tokens).

        Args:
            prompt: Промпт для анализа

        Returns:
            LLMClient: Основной или fallback клиент
        """
        estimated_tokens = self._estimate_prompt_tokens(prompt)
        threshold = Config.LLM_FALLBACK_THRESHOLD

        if estimated_tokens > threshold:
            logger.warning(
                f"⚠️ Large PR detected: ~{estimated_tokens} tokens " f"(threshold: {threshold}). Using fallback model."
            )

            # Lazy init fallback client
            if self.fallback_client is None:
                self.fallback_client = LLMClient(
                    model=Config.LLM_FALLBACK_MODEL,
                    max_tokens=Config.LLM_MAX_TOKENS,
                    temperature=Config.LLM_TEMPERATURE,
                )
                logger.info(f"📦 Fallback model initialized: {Config.LLM_FALLBACK_MODEL}")

            return self.fallback_client

        return self.client

    @async_retry_on_invalid_json(max_attempts=3, wait_seconds=0)
    async def analyze_pr(self, pr_context: Dict[str, Any], agents_md_content: str = None) -> Dict[str, Any]:
        """
        Асинхронно анализирует Pull Request и генерирует review с inline комментариями.

        Декоратор @async_retry_on_invalid_json автоматически повторяет попытки при:
            • JSONDecodeError: LLM вернула невалидный JSON
            • ValueError: LLM вернула невалидную структуру
            • Максимум 3 попытки без задержки

        Args:
            pr_context: Dictionary с деталями PR из GitHub
            agents_md_content: Содержимое AGENTS.md файла из репозитория (опционально)

        Returns:
            Dictionary с review summary и inline comments

        Raises:
            json.JSONDecodeError: Если LLM не вернула валидный JSON после 3 попыток
        """
        pr = pr_context["pr"]
        files = pr_context["files"]

        # Build prompt with PR context and AGENTS.md
        prompt = self._build_review_prompt(pr, files, agents_md=agents_md_content)

        # Choose appropriate client based on prompt size
        client = self._get_client_for_prompt(prompt)

        # Call LLM for detailed analysis
        try:
            review_text = await client.generate(user_prompt=prompt, system_prompt=ReviewPrompts.SYSTEM_PROMPT)

            # Extract JSON from response (removes markdown blocks if present)
            json_text = self._extract_json_from_response(review_text)

            # Parse JSON - if invalid, will trigger retry via decorator
            result = json.loads(json_text)

            # Validate structure - if invalid, will trigger retry via decorator
            if not isinstance(result, dict):
                raise ValueError("LLM returned non-dict JSON")

            if "summary" not in result:
                raise ValueError("Missing 'summary' in LLM response")

            # Normalize structure
            return {
                "summary": result.get("summary", ""),
                "critical_issues": result.get("critical_issues", []),
                "suggestions": result.get("suggestions", []),
                "inline_comments": result.get("inline_comments", []),
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"⚠️ Invalid response from LLM: {e}")
            # Re-raise for retry through decorator
            raise
        except Exception as e:
            # Other errors (e.g., network issues) - don't retry, return error response
            logger.error(f"Error calling LLM: {e}", exc_info=True)
            return self._get_error_response()

    def _build_review_prompt(self, pr: Dict[str, Any], files: List[Dict[str, Any]], agents_md: str = None) -> str:
        """Build prompt for detailed review with all changed files."""

        file_changes = []
        # Include all files with full patches
        for file in files:
            if file["patch"]:
                file_changes.append(
                    f"""
### File: {file['filename']} ({file['status']})
Changes: +{file['additions']} -{file['deletions']}

```diff
{file['patch']}
```
"""
                )

        changes_text = "\n".join(file_changes)

        return ReviewPrompts.get_detailed_review_prompt(pr, changes_text, agents_md=agents_md)

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON from LLM response, removing markdown wrappers and comments.

        Handles cases:
        - ```json {...} ```
        - ``` {...} ```
        - {...}
        - Text before/after JSON

        Args:
            response: Raw response from LLM

        Returns:
            Cleaned JSON text
        """
        text = response.strip()

        # Remove markdown blocks
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first line (```json or ```)
            if lines[0].strip() in ["```json", "```"]:
                lines = lines[1:]
            # Remove last line if it's ```
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        # Find JSON object
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx != -1 and end_idx != -1:
            text = text[start_idx : end_idx + 1]

        return text

    def _get_error_response(self) -> Dict[str, Any]:
        """Return error response when analysis fails."""
        return {
            "summary": ReviewPrompts.get_error_response(),
            "inline_comments": [],
            "is_large_pr": False,
        }
