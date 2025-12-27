# 🧪 Обновление тестов для Async

## ✅ Что сделано:

### 1. Добавлены зависимости
```toml
pytest-asyncio = "^0.21.0"  # Для async тестов
pytest-mock = "^3.12.0"      # Для AsyncMock
```

### 2. Обновлены тесты

#### test_llm_integration.py
- ✅ Добавлен `@pytest.mark.asyncio` на класс
- ✅ Все `def test_...` → `async def test_...`
- ✅ Все `llm_client.generate()` → `await llm_client.generate()`
- ✅ Все `code_analyzer.analyze_pr()` → `await code_analyzer.analyze_pr()`

#### test_retry_logic.py
- ✅ Добавлен `@pytest.mark.asyncio` на класс
- ✅ Все тесты стали async
- ✅ Используется `AsyncMock` вместо обычного `Mock`
- ✅ `patch.object(..., new_callable=AsyncMock)` для async методов
- ✅ Все вызовы с `await`

### 3. Конфигурация pytest

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"  # Автоматическое определение async тестов
```

## 🧪 Запуск тестов:

### Все тесты
```bash
pytest
```

### Только unit тесты (без LLM API)
```bash
pytest -m unit
```

### Только integration тесты (требуют LLM_API_KEY)
```bash
export LLM_API_KEY=your_key
pytest -m integration
```

### Конкретный файл
```bash
pytest tests/test_retry_logic.py -v
```

### С покрытием
```bash
pytest --cov=src --cov-report=html
```

## 📝 Изменения в mock'ах:

### До (синхронный):
```python
with patch.object(analyzer.client, "generate", return_value="response") as mock:
    result = analyzer.analyze_pr(pr_context)
    assert mock.call_count == 1
```

### После (асинхронный):
```python
with patch.object(analyzer.client, "generate",
                  new_callable=AsyncMock,
                  return_value="response") as mock:
    result = await analyzer.analyze_pr(pr_context)
    assert mock.call_count == 1
```

## ⚠️ Важные моменты:

1. **AsyncMock для async функций**
   - Всегда используй `new_callable=AsyncMock`
   - Для `side_effect` тоже нужен AsyncMock

2. **await для всех async вызовов**
   - `await llm_client.generate(...)`
   - `await code_analyzer.analyze_pr(...)`

3. **@pytest.mark.asyncio**
   - Можно на класс или на отдельные функции
   - С `asyncio_mode = "auto"` можно не писать

4. **Fixtures остаются синхронными**
   - `@pytest.fixture` не меняется
   - Только тестовые функции становятся async

## 🎯 Покрытие тестами:

- ✅ **LLM client** - создание, генерация, code review
- ✅ **Code analyzer** - анализ PR, валидация JSON
- ✅ **Retry logic** - все сценарии retry
- ✅ **Webhook handler** - парсинг events (синхронный)

## 🚀 Готово к использованию!

Все тесты обновлены и совместимы с новой async архитектурой.
