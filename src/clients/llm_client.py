"""
LLM client для code review через Anthropic-совместимое API.
Использует нативный Anthropic Messages API для поддержки thinking mode.
Полностью асинхронный на основе httpx.AsyncClient.
"""

import logging
from typing import Optional

import httpx

from src.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Асинхронный клиент для работы с Claude через Anthropic Messages API.

    Использует httpx.AsyncClient для истинной асинхронности без thread pool.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[int] = None,
    ):
        """
        Инициализация LLM клиента.

        Args:
            model: Название модели (по умолчанию из Config)
            temperature: Температура генерации (0.0-2.0)
            max_tokens: Максимальное количество токенов в ответе
            timeout: Таймаут запроса в секундах
        """
        # Параметры модели
        self.model = model or Config.LLM_MODEL
        self.temperature = temperature if temperature is not None else Config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or Config.LLM_MAX_TOKENS
        self.timeout = timeout or Config.LLM_TIMEOUT

        # API настройки
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_API_BASE_URL

        # Thinking mode настройки
        self.enable_thinking = Config.LLM_ENABLE_THINKING
        self.thinking_budget = Config.LLM_THINKING_BUDGET_TOKENS

        # Claude требует temperature = 1.0 для thinking mode
        if self.enable_thinking and self.temperature != 1.0:
            logger.warning(f"⚠️ Thinking mode требует temperature=1.0, изменяю с {self.temperature} на 1.0")
            self.temperature = 1.0

        # Валидация
        if not self.api_key:
            logger.error("❌ LLM_API_KEY is not set!")
            raise ValueError("LLM_API_KEY environment variable is required")

        logger.info(
            f"🤖 Async LLM Client initialized: model={self.model}, "
            f"temp={self.temperature}, max_tokens={self.max_tokens}, "
            f"thinking_mode={'enabled' if self.enable_thinking else 'disabled'}"
        )

    async def generate(self, user_prompt: str, system_prompt: str) -> str:  # noqa: C901
        """
        Асинхронно генерирует ответ через Anthropic Messages API.

        Args:
            user_prompt: Запрос пользователя
            system_prompt: Системный промпт с инструкциями

        Returns:
            Ответ модели в виде строки

        Raises:
            ValueError: Если LLM вернула пустой ответ
            Exception: При ошибках API
        """
        # Подготовка endpoint
        base_url = self.base_url.rstrip("/")
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]
        endpoint = f"{base_url}/v1/messages"

        # Payload
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        # System prompt
        if system_prompt and system_prompt.strip():
            payload["system"] = system_prompt

        # Thinking mode
        if self.enable_thinking:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }
            logger.debug(f"🧠 Thinking mode enabled with budget: {self.thinking_budget} tokens")

        # Headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.debug(f"📤 Calling Anthropic API (async): {endpoint}")

        try:
            # Async API call with httpx.AsyncClient
            async with httpx.AsyncClient(timeout=self.timeout, verify=False) as client:
                response = await client.post(endpoint, json=payload, headers=headers)

            if response.status_code != 200:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(f"❌ {error_msg}")
                raise Exception(error_msg)

            data = response.json()
            logger.debug(f"✅ API response received: {data.get('id', 'N/A')}")

            # Логируем usage
            usage = data.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            logger.info(f"📊 Tokens: input={input_tokens}, output={output_tokens}, " f"total={input_tokens + output_tokens}")

            # Извлекаем текстовый ответ
            content_blocks = data.get("content", [])
            text_parts = []

            for block in content_blocks:
                block_type = block.get("type")

                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "thinking":
                    # Thinking логируем, но не включаем в ответ
                    thinking = block.get("thinking", "")
                    logger.debug(f"🧠 Thinking: {thinking[:200]}...")

            content = "\n".join(text_parts).strip()

            # Валидация ответа
            if not content:
                logger.error("❌ LLM returned empty response")
                raise ValueError("LLM returned empty response")

            logger.debug(f"✅ LLM response: {len(content)} chars")
            return content

        except httpx.TimeoutException:
            logger.error(f"❌ API timeout after {self.timeout}s")
            raise
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            raise
