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
from tenacity import AsyncRetrying, before_sleep_log, retry_if_exception_type, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    max_attempts: int = 3,
    wait_seconds: float = 1.0,
) -> Callable:
    """
    Декоратор для async функций с retry при HTTP ошибках.

    Автоматически повторяет запрос при:
    - httpx.HTTPError (включая 4xx, 5xx)
    - httpx.TimeoutException
    - httpx.RemoteProtocolError

    Args:
        max_attempts: Максимальное количество попыток (по умолчанию 3)
        wait_seconds: Задержка между попытками в секундах (по умолчанию 1.0)

    Returns:
        Декоратор для async функции

    Usage:
        @async_retry_on_http_errors(max_attempts=3, wait_seconds=1.0)
        async def call_api(self, endpoint: str):
            response = await client.get(endpoint)
            return response.json()
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(max_attempts),
                wait=wait_fixed(wait_seconds),
                retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
                before_sleep=before_sleep_log(logger, logging.WARNING),
            ):
                with attempt:
                    return await func(*args, **kwargs)

        return wrapper

    return decorator
