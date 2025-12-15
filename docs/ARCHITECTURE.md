# 🏗️ Архитектура MergeBlocker

## Обзор

MergeBlocker - это GitHub App, который автоматически делает code review для Pull Requests с использованием Claude AI.

## Компоненты системы

### 1. Flask Server (`app.py`)

**Основной сервер приложения.**

- Принимает webhooks от GitHub
- Валидирует signature для безопасности
- Координирует процесс review
- Управляет жизненным циклом запросов

**Ключевые эндпоинты:**
- `GET /` - Health check
- `POST /webhook` - Прием GitHub webhooks

### 2. Webhook Handler (`webhook_handler.py`)

**Отвечает за обработку GitHub webhooks.**

**Функции:**
- `verify_signature()` - Проверка HMAC signature
- `parse_event()` - Парсинг webhook payload
- `should_process_pr_event()` - Фильтрация событий
- `extract_pr_info()` - Извлечение метаданных PR

**Обрабатываемые события:**
- `pull_request.opened`
- `pull_request.reopened`
- `pull_request.synchronize`
- `pull_request.ready_for_review`

### 3. GitHub Client (`github_client.py`)

**Клиент для взаимодействия с GitHub API.**

**Функции:**
- `get_installation_client()` - Получение клиента с JWT auth
- `get_pr_context()` - Сбор полного контекста PR
- `create_review()` - Создание review с inline комментариями
- `create_comment()` - Создание простого комментария
- `create_check_run()` - Создание/обновление Check Run

**Использует:**
- `PyGithub` для работы с GitHub API
- JWT для аутентификации GitHub App
- Installation tokens для доступа к репозиториям

### 4. Code Analyzer (`code_analyzer.py`)

**Анализирует код с помощью Claude AI.**

**Стратегии анализа:**

#### Small PR (≤20 файлов, ≤800 строк)
- Полный анализ всех изменений
- Детальные inline комментарии (до 10 шт)
- Comprehensive summary

#### Large PR (>20 файлов или >800 строк)
- High-level overview
- Только summary без inline
- Рекомендации по разбиению

**Функции:**
- `analyze_pr()` - Главная функция анализа
- `_analyze_small_pr()` - Детальный анализ
- `_analyze_large_pr()` - Summary для больших PR
- `quick_check()` - Быстрые детерминированные проверки

**Что проверяется:**

**Quick Checks (детерминированные):**
- Потенциальные секреты (regex patterns)
- TODO/FIXME в новом коде
- Размер PR

**AI Analysis (Claude):**
- Security vulnerabilities
- Potential bugs
- Edge cases
- Code quality
- Best practices
- Performance concerns
- Testing coverage

### 5. Review Formatter (`review_formatter.py`)

**Форматирует результаты review для GitHub.**

**Функции:**
- `format_review_comment()` - Основной review комментарий
- `format_inline_comment()` - Inline комментарий с AI badge
- `format_error_comment()` - Сообщение об ошибке
- `format_check_run_summary()` - Summary для Check Run

**Форматы вывода:**
- Markdown для GitHub comments
- Structured data для Check Runs
- Emoji для визуальной индикации

### 6. Config (`config.py`)

**Управление конфигурацией.**

- Загрузка из `.env` файла
- Валидация обязательных параметров
- Чтение private key
- Типизированные настройки

## Поток данных

```
┌──────────────────────────────────────────────────────────────┐
│                         GitHub                                │
│                                                               │
│  User creates/updates PR                                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ webhook POST /webhook
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                    Flask Server (app.py)                      │
│                                                               │
│  1. Receive webhook                                           │
│  2. Verify signature (WebhookHandler)                         │
│  3. Parse event (WebhookHandler)                              │
│  4. Filter event (should_process?)                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ if processable
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              GitHub Client (github_client.py)                 │
│                                                               │
│  1. Get installation token (JWT auth)                         │
│  2. Fetch PR details                                          │
│  3. Get file changes & diffs                                  │
│  4. Get commits, labels, etc.                                 │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ PR context dict
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              Code Analyzer (code_analyzer.py)                 │
│                                                               │
│  1. Determine strategy (small vs large PR)                    │
│  2. Quick checks (secrets, TODOs, size)                       │
│  3. Build prompt with context                                 │
│  4. Call Claude API                                           │
│  5. Parse response                                            │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ review result dict
                         ▼
┌──────────────────────────────────────────────────────────────┐
│          Review Formatter (review_formatter.py)               │
│                                                               │
│  1. Format main review comment                                │
│  2. Format inline comments                                    │
│  3. Format check run summary                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ formatted strings
                         ▼
┌──────────────────────────────────────────────────────────────┐
│              GitHub Client (github_client.py)                 │
│                                                               │
│  1. Create review with inline comments                        │
│  2. Create/update check run                                   │
│  3. Handle errors gracefully                                  │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ API calls
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                         GitHub                                │
│                                                               │
│  - Review comment posted                                      │
│  - Inline comments added                                      │
│  - Check run status updated                                   │
└──────────────────────────────────────────────────────────────┘
```

## Аутентификация

### GitHub App Authentication

MergeBlocker использует двухэтапную аутентификацию:

1. **JWT Token** (короткоживущий)
   - Создается из App ID + Private Key
   - Используется для получения installation token
   - Срок жизни: 10 минут

2. **Installation Token** (долгоживущий)
   - Получается через JWT
   - Привязан к конкретной установке App
   - Используется для всех API запросов
   - Срок жизни: 1 час (обновляется автоматически)

```python
# Упрощенный пример
integration = GithubIntegration(app_id, private_key)
access_token = integration.get_access_token(installation_id)
client = Github(access_token)
```

### Webhook Signature Verification

Все webhooks проверяются HMAC-SHA256 signature:

```python
mac = hmac.new(secret, request.data, hashlib.sha256)
expected = 'sha256=' + mac.hexdigest()
valid = hmac.compare_digest(signature, expected)
```

## Безопасность

### Защита Private Key

- Хранится в файле `private-key.pem`
- Исключен из git (`.gitignore`)
- Читается только при старте
- Не логируется

### Webhook Secret

- Используется для HMAC подписи
- Хранится в environment variable
- Проверяется для каждого запроса

### Rate Limiting

**GitHub API limits:**
- 5000 requests/hour per installation
- Текущая реализация не достигает лимита

**Claude API limits:**
- Зависит от плана
- Обрабатывается через try/except

## Масштабирование

### Текущая архитектура (MVP)

- Синхронная обработка
- Один worker
- Подходит для <50 PR/день

### Production рекомендации

#### 1. Асинхронная обработка

```python
# Вместо прямого вызова
process_pr_review(pr_info)

# Использовать queue
celery_app.send_task('review_pr', args=[pr_info])
```

**Стек:**
- Celery + Redis
- RabbitMQ (альтернатива)

#### 2. Кэширование

```python
# Кэш installation tokens (1 час)
# Кэш PR contexts (5 минут)
# Redis как storage
```

#### 3. Database

**Что хранить:**
- История reviews (для аналитики)
- Last reviewed SHA (избежать дубликатов)
- User preferences
- Rate limiting counters

**Схема:**
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    repo_full_name VARCHAR(255),
    pr_number INTEGER,
    head_sha VARCHAR(40),
    status VARCHAR(50),
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    inline_comments_count INTEGER
);

CREATE INDEX idx_repo_pr ON reviews(repo_full_name, pr_number);
```

#### 4. Мониторинг

**Metrics:**
- Review processing time
- API call latency
- Error rates
- Queue depth

**Tools:**
- Prometheus + Grafana
- Sentry для ошибок
- CloudWatch (AWS)

## Обработка ошибок

### Стратегия

1. **Graceful degradation**: если AI fails → post simple comment
2. **Retry logic**: для GitHub API (с exponential backoff)
3. **Logging**: все ошибки в logs
4. **User feedback**: error comments в PR

### Примеры

```python
try:
    review = code_analyzer.analyze_pr(context)
except Exception as e:
    logger.error(f"Analysis failed: {e}")
    # Fallback to simple comment
    github_client.create_comment(
        body="⚠️ AI review failed, please review manually"
    )
```

## Расширения

### Planned Features

1. **Manual trigger**: комментарий `/review` для повторного анализа
2. **Config file**: `.github/mergeblocker.yml` в репозитории
3. **Custom rules**: per-repo настройки
4. **Multiple LLM providers**: GPT-4, Gemini support
5. **Code suggestions**: automatic fix proposals
6. **Learning mode**: улучшение через feedback

### Интеграции

- **Jira**: link to issues
- **Slack**: notifications
- **Datadog**: metrics
- **GitHub Actions**: trigger on specific conditions

## Тестирование

### Unit Tests (будущее)

```python
# test_webhook_handler.py
def test_verify_signature():
    handler = WebhookHandler()
    request = MockRequest(...)
    assert handler.verify_signature(request) == True

# test_code_analyzer.py
def test_analyze_small_pr():
    analyzer = CodeAnalyzer()
    result = analyzer.analyze_pr(mock_context)
    assert 'summary' in result
```

### Integration Tests

```python
# test_github_client.py
def test_create_review():
    client = GitHubClient()
    success = client.create_review(...)
    assert success == True
```

### E2E Tests

```bash
# 1. Start server
# 2. Simulate webhook
# 3. Check PR for comment
```

## Deployment

### Heroku

```bash
heroku create mergeblocker
heroku config:set GITHUB_APP_ID=...
git push heroku main
```

### Docker

```bash
docker build -t mergeblocker .
docker run -p 8000:8000 --env-file .env mergeblocker
```

### AWS

- **ECS**: Container orchestration
- **Lambda**: Serverless option (холодный старт - проблема)
- **ALB**: Load balancer
- **RDS**: Database
- **ElastiCache**: Redis

## Метрики успеха

### Technical

- Latency: <60s для review
- Uptime: >99%
- Error rate: <1%

### Product

- Reviews/day
- Bugs caught
- User satisfaction
- Adoption rate

## FAQ

**Q: Почему Flask, а не FastAPI?**
A: Flask проще для MVP. FastAPI - хороший выбор для production.

**Q: Почему синхронная обработка?**
A: Для MVP достаточно. В production нужен Celery.

**Q: Как обновить review при новом push?**
A: Event `pull_request.synchronize` триггерит новый анализ.

**Q: Можно ли использовать другую LLM?**
A: Да, нужно реализовать adapter в `code_analyzer.py`.

---

**Версия документа:** 1.0.0
**Последнее обновление:** 2024-12-14
