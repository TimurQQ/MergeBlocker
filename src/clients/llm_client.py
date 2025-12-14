"""
LLM client для code review через OpenRouter-совместимое API.
Базируется на архитектуре из ML-API проекта.
"""

import logging
from typing import Optional

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.config import Config

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Клиент для работы с LLM через OpenAI-совместимое API.

    Использует LangChain для удобной интеграции.
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
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            timeout: Таймаут запроса в секундах
        """
        # Используем значения из Config или переданные параметры
        self.model = model or Config.LLM_MODEL
        self.temperature = temperature if temperature is not None else Config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or Config.LLM_MAX_TOKENS
        self.timeout = timeout or Config.LLM_TIMEOUT

        # API настройки
        self.api_key = Config.LLM_API_KEY
        self.base_url = Config.LLM_API_BASE_URL

        # Валидация
        if not self.api_key:
            logger.error("❌ LLM_API_KEY is not set!")
            raise ValueError("LLM_API_KEY environment variable is required")

        # Создаем LangChain LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,  # Используем api_key вместо openai_api_key
            base_url=self.base_url,  # Используем base_url вместо openai_api_base
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=3,  # Встроенные retry LangChain
            timeout=self.timeout,  # timeout вместо request_timeout
        )

        logger.info(f"🦜 LLM Client initialized: model={self.model}, " f"temp={self.temperature}, base_url={self.base_url}")

    def generate(self, user_prompt: str, system_prompt: str) -> str:
        """
        Синхронный метод для взаимодействия с LLM.

        Args:
            user_prompt: Запрос пользователя
            system_prompt: Системный промпт с инструкциями

        Returns:
            Ответ модели в виде строки

        Raises:
            ValueError: Если LLM вернула пустой ответ
        """
        # Создаем сообщения
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        try:
            # Синхронный вызов через invoke
            result = self.llm.invoke(messages)

            # Извлекаем контент
            content = result.content if result.content else ""

            if not content or not content.strip():
                logger.error("❌ LLM returned empty response")
                raise ValueError("LLM returned empty response")

            logger.debug(f"✅ LLM response: {len(content)} chars")

            return content

        except Exception as e:
            logger.error(f"❌ LLM error: {e}")
            raise
