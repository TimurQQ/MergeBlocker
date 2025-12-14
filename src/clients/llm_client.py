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
        timeout: Optional[int] = None
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
        
        # Создаем LangChain LLM
        self.llm = ChatOpenAI(
            model=self.model,
            openai_api_key=self.api_key,
            openai_api_base=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            max_retries=3,  # Встроенные retry LangChain
            request_timeout=self.timeout,
        )
        
        logger.info(
            f"🦜 LLM Client initialized: model={self.model}, "
            f"temp={self.temperature}, base_url={self.base_url}"
        )
    
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

