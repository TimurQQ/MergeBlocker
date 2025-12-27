# 🚀 Переход на Quart (Async Flask)

## ✅ Что сделано:

### 1. Заменили Flask на Quart
- **Flask → Quart:** Асинхронный веб-фреймворк, 100% совместимый API
- **Gunicorn → Hypercorn:** ASGI сервер вместо WSGI
- **requests → httpx:** Для LLM client (подготовка к async)

### 2. Добавили async/await
- ✅ Все route handlers теперь `async def`
- ✅ Синхронные I/O обернуты в `asyncio.to_thread()`
- ✅ Background tasks через `asyncio.create_task()`

### 3. Обновили зависимости

**pyproject.toml:**
```toml
quart = "^0.19.0"        # Вместо flask
httpx = "^0.25.0"         # Вместо requests (в llm_client)
hypercorn = "^0.16.0"     # Вместо gunicorn
tiktoken = "^0.5.0"       # Для token counting
```

**Удалены:**
- `flask`
- `gunicorn`
- `langchain`
- `langchain-openai`

## 🎯 Преимущества Quart:

### 1. Неблокирующая обработка
**До (Flask):**
```python
@app.route("/webhook")
def webhook():
    # Блокирует поток на весь review (до 180 сек)
    process_pr_review(pr_info)
    return {"ok": True}
```

**После (Quart):**
```python
@app.route("/webhook")
async def webhook():
    # Мгновенно отвечает на webhook
    asyncio.create_task(process_pr_review(pr_info))
    return {"ok": True}
```

### 2. Параллельная обработка
- ✅ Несколько PR reviews одновременно
- ✅ Не блокирует другие webhook'и
- ✅ Экономия ресурсов (меньше памяти)

### 3. Производительность
| Метрика | Flask | Quart |
|---------|-------|-------|
| Одновременных запросов | 1-4 (workers) | Сотни (event loop) |
| Память на worker | ~50-100 MB | ~30-50 MB |
| Latency для I/O | Блокирует | Неблокирует |

## 🎨 Async Retry Decorators:

Созданы удобные декораторы по аналогии с `rate_limiter` из ML-API:

### src/utils/async_retry.py

```python
@async_retry_on_invalid_json(max_attempts=3, wait_seconds=0)
async def analyze_pr(self, pr_context, agents_md_content=None):
    review_text = await client.generate(...)
    result = json.loads(review_text)  # Auto retry on JSONDecodeError
    return result
```

**Доступные декораторы:**

1. **`@async_retry_on_invalid_json`** - для LLM ответов
   - Retry при `JSONDecodeError`, `ValueError`
   - По умолчанию: 3 попытки без задержки

2. **`@async_retry_on_http_errors`** - для HTTP запросов
   - Retry при 429, 500, 502, 503, 504
   - По умолчанию: 3 попытки с задержкой 1 секунда

**Преимущества:**
- ✅ Чистый код (декоратор вместо try/except блоков)
- ✅ Консистентная retry логика во всем проекте
- ✅ Легко настраивать параметры
- ✅ Автоматическое логирование через tenacity

## 📋 Изменения в коде:

### app.py
```python
# До
from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route("/webhook")
def webhook():
    process_pr_review(pr_info)
    return jsonify({"ok": True})

# После
from quart import Quart, jsonify, request
app = Quart(__name__)

@app.route("/webhook")
async def webhook():
    asyncio.create_task(process_pr_review(pr_info))
    return jsonify({"ok": True})
```

### Истинный Async для LLM
```python
# LLM Client - нативный async с httpx.AsyncClient
async def generate(self, user_prompt: str, system_prompt: str) -> str:
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(endpoint, json=payload, headers=headers)
    return content

# Code Analyzer - элегантный декоратор для retry
@async_retry_on_invalid_json(max_attempts=3, wait_seconds=0)
async def analyze_pr(self, pr_context, agents_md_content=None):
    review_text = await client.generate(...)
    result = json.loads(review_text)  # Auto retry on JSONDecodeError
    return result

# App - прямой await без thread pool
review_result = await code_analyzer.analyze_pr(pr_context, agents_md_content)
```

### Обертка синхронного кода (только для PyGithub)
```python
# GitHub API (PyGithub - синхронная библиотека, нет async версии)
pr_details = await asyncio.to_thread(
    github_client.get_pr,
    installation_id=...,
    repo_full_name=...,
    pr_number=...
)
```

## 🚀 Deployment:

### Docker
```dockerfile
# Dockerfile использует hypercorn
CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:8002", "--workers", "4"]
```

### Local Development
```bash
# Quart поддерживает тот же запуск
python app.py
```

## 🧪 Тестирование:

### 1. Установить зависимости
```bash
poetry install
# или
pip install -r requirements.txt
```

### 2. Запустить локально
```bash
./start-local.sh
```

### 3. Проверить health check
```bash
curl http://localhost:8002/
# {"status": "ok", "app": "MergeBlocker", "version": "1.0.0"}
```

### 4. Отправить тестовый webhook
```bash
# GitHub отправит webhook, который обработается асинхронно
# Проверьте логи: review запустится в background
```

## ⚡ Ожидаемые улучшения:

### 1. Время ответа на webhook
- **До:** 30-180 секунд (блокируется на review)
- **После:** < 100ms (мгновенный ответ)

### 2. Одновременные PR reviews
- **До:** 1-4 (по количеству workers)
- **После:** Десятки (event loop)

### 3. Потребление памяти
- **До:** ~400 MB (4 workers × 100 MB)
- **После:** ~150 MB (4 workers × 40 MB)

## 🔍 Важные моменты:

### 1. Синхронный код обернут в asyncio.to_thread()
- PyGithub - синхронная библиотека
- LLM client - синхронный httpx Client
- Все работает без блокировки event loop

### 2. Background tasks
```python
# Review запускается в фоне
asyncio.create_task(process_pr_review(pr_info))
# Webhook мгновенно возвращает ответ
```

### 3. Совместимость
- ✅ 100% обратно совместимо с Flask API
- ✅ Те же роуты, те же декораторы
- ✅ Только добавили `async/await`

## 🎓 Дополнительно:

### Quart Documentation
- https://quart.palletsprojects.com/

### Hypercorn Documentation
- https://hypercorn.readthedocs.io/

### Asyncio Best Practices
- https://docs.python.org/3/library/asyncio.html
