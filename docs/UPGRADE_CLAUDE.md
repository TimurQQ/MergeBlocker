# 🚀 Обновление MergeBlocker: Claude 4.5 Sonnet + Quart + Thinking Mode

## ✅ Что было сделано:

### 0. Переход на Quart (Async)
- ✅ **Flask → Quart:** Асинхронный веб-фреймворк
- ✅ **Gunicorn → Hypercorn:** ASGI сервер
- ✅ **requests → httpx:** Async-ready HTTP client
- ✅ Все endpoints теперь `async def`
- ✅ Background tasks через `asyncio.create_task()`

**Подробности:** См. `QUART_MIGRATION.md`

### 1. Обновлен Config (src/config.py)
- **Модель:** `eliza-Claude-Sonnet-4-5` (вместо DeepSeek)
- **Max tokens:** 64000 (вместо 4000)
- **Temperature:** 1.0 (вместо 0.3)
- **Thinking mode:** Включен по умолчанию
- **Budget tokens:** 10000 для thinking
- **Fallback:** Gemini 3 Pro для PR > 100k tokens

### 2. Обновлен LLM Client (src/clients/llm_client.py)
- ✅ **Полностью асинхронный** с `httpx.AsyncClient`
- ✅ **Нативный Anthropic Messages API** (убран LangChain)
- ✅ Прямая поддержка thinking mode с budget_tokens
- ✅ Извлечение thinking блоков и логирование
- ✅ Истинный async без `asyncio.to_thread()`

**Почему не LangChain?**
- Thinking mode через прокси требует точного контроля параметров
- LangChain может не поддерживать budget_tokens через QYP прокси
- Нативный HTTP дает 100% контроль над API

**Почему httpx.AsyncClient, а не asyncio.to_thread()?**
- ✅ Истинная асинхронность без thread pool overhead
- ✅ Лучшая производительность для I/O операций
- ✅ Более чистый код

### 3. Обновлен Code Analyzer (src/analysis/code_analyzer.py)
- ✅ Оценка размера промпта (~1 токен = 4 символа)
- ✅ Автоматический fallback на Gemini 3 Pro для больших PR
- ✅ Lazy initialization fallback клиента

## 📋 Новые ENV переменные:

```bash
# Обновленные значения по умолчанию
LLM_MODEL=eliza-Claude-Sonnet-4-5
LLM_TEMPERATURE=1.0
LLM_MAX_TOKENS=64000

# Новые параметры
LLM_ENABLE_THINKING=true                          # Включить thinking mode
LLM_THINKING_BUDGET_TOKENS=10000                  # Лимит на рассуждения
LLM_FALLBACK_MODEL=eliza-Gemini-3-Pro-Preview     # Для больших PR
LLM_FALLBACK_THRESHOLD=100000                     # Порог в токенах
```

## 🎯 Как работает Thinking Mode:

### Без Thinking (старый подход):
```
Prompt (10k tokens) → Model → Answer (2k tokens)
```

### С Thinking (новый подход):
```
Prompt (10k tokens) → Model:
  1. Thinking (до 10k tokens, логируется)
  2. Answer (до 54k tokens)
```

### Преимущества:
- 🧠 Более глубокий анализ кода
- 🔍 Лучше находит edge cases
- 📊 Более структурированные ответы
- 💬 Понятное объяснение решений

## 🔄 Логика Fallback:

```python
if estimated_tokens > 100000:  # ~400k символов
    # Используем Gemini 3 Pro (1M контекст)
    model = "eliza-Gemini-3-Pro-Preview"
else:
    # Используем Claude 4.5 Sonnet (200k контекст)
    model = "eliza-Claude-Sonnet-4-5"
```

## 📊 Ожидаемые метрики:

### Claude 4.5 Sonnet:
- **Контекст:** 200k tokens (~800k символов)
- **Thinking budget:** 10k tokens
- **Max output:** 64k tokens
- **Качество:** ⭐⭐⭐⭐⭐ (best for code)

### Gemini 3 Pro (fallback):
- **Контекст:** 1M tokens (~4M символов)
- **Max output:** 64k tokens
- **Качество:** ⭐⭐⭐⭐ (good for large context)

## 🧪 Тестирование:

### 1. Локальный тест:
```bash
cd /Users/timtim2379/Desktop/work_dir/py_scripts/merge-bloker
./start-local.sh
```

### 2. Создать тестовый PR в GitHub

### 3. Проверить логи:
```bash
docker logs mergeblocker -f
```

Ищем:
- ✅ `🧠 Thinking mode enabled`
- ✅ `🧠 Thinking: ...` (логи рассуждений)
- ✅ `📊 Tokens: input=XXX, output=YYY`

## ⚠️ Важные моменты:

1. **max_tokens > budget_tokens**
   - Иначе API вернет ошибку 400

2. **Thinking логируется, но не включается в ответ**
   - Пользователь видит только финальный answer

3. **Fallback срабатывает автоматически**
   - Для PR с большим количеством файлов

4. **Модель в логах:**
   - Claude: `🔄 Using native Anthropic API for Claude`
   - Others: `🔄 Using LangChain for non-Claude models`

## 🚀 Готово к деплою!

После успешного локального теста:
```bash
git add .
git commit -m "Upgrade to Claude 4.5 Sonnet with thinking mode"
git push
```

CI/CD автоматически:
1. Запустит тесты
2. Задеплоит на сервер
3. Перезапустит контейнер
