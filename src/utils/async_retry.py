"""
Async retry decorators for handling transient errors.

Provides convenient decorators for async functions that may fail temporarily,
such as LLM API calls returning invalid JSON.
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Type, TypeVar

import httpx
from tenacity import AsyncRetrying, before_sleep_log, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_fixed

logger = logging.getLogger(__name__)

T = TypeVar("T")


class LLMRetryableError(Exception):
    """
    Признак того что ошибка LLM API временная и запрос можно повторить.

    Бросается для 429 (rate-limit / inflight limit) и 5xx (server error),
    чтобы decorator async_retry_on_http_errors мог их подхватить.
    Для 4xx (кроме 429) бросаем обычный Exception — повторять бессмысленно.
    """


def async_retry_on_invalid_json(
    max_attempts: int = 3,
    wait_seconds: float = 0,
    exceptions: tuple[Type[Exception], ...] = (json.JSONDecodeError, ValueError),
) -> Callable:
    """
    Декоратор для async функций с retry при невалидном JSON ответе от LLM.

    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        wait_seconds: Задержка между попытками в секундах (по умолчанию 0)
        exceptions: Tuple исключений для retry (по умолчанию JSONDecodeError, ValueError)

    Returns:
        Декоратор для async функции

    Usage:
        @async_retry_on_invalid_json(max_attempts=3)
        async def analyze_pr(self, pr_context: dict):
            result = await llm.generate(...)
            return json.loads(result)  # Retry if invalid JSON
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            # Используем AsyncRetrying из tenacity
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_fixed(wait_seconds),
                retry=retry_if_exception_type(exceptions),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    return await func(*args, **kwargs)

        return wrapper

    return decorator


def async_retry_on_http_errors(
    max_attempts: int = 5,
    wait_min: float = 2.0,
    wait_max: float = 30.0,
) -> Callable:
    """
    Декоратор для async функций с retry при transient HTTP ошибках.

    Автоматически повторяет запрос при:
    - httpx.HTTPError (включая HTTPStatusError для 4xx/5xx, TimeoutException, ConnectError)
    - LLMRetryableError (наш собственный класс для 429 / 5xx от LLM-шлюза,
      которые пришли как валидный HTTP 200/4xx/5xx, но логически временные)

    Использует экспоненциальный back-off: wait_min, wait_min*2, wait_min*4, ... до wait_max.
    Это критично для случаев inflight-limit на шлюзе — фиксированной задержки не хватает,
    нужно дать соседним клиентам отпустить слоты.

    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 5)
        wait_min: Минимальная задержка между попытками (по умолчанию 2.0с)
        wait_max: Максимальная задержка между попытками (по умолчанию 30.0с)

    Returns:
        Декоратор для async функции

    Usage:
        @async_retry_on_http_errors(max_attempts=5, wait_min=2.0, wait_max=30.0)
        async def call_api(self, endpoint: str):
            response = await client.get(endpoint)
            if response.status_code == 429 or response.status_code >= 500:
                raise LLMRetryableError(...)
            return response.json()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max),
                retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException, LLMRetryableError)),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    return await func(*args, **kwargs)

        return wrapper

    return decorator
