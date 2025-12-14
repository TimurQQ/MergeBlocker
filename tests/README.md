# Тесты для MergeBlocker

## 📁 Структура

```
tests/
├── __init__.py
├── conftest.py                # Pytest fixtures
├── test_webhook_handler.py    # Тесты обработчика webhook
├── test_llm_integration.py    # Интеграционные тесты LLM (требуют API key)
└── README.md                  # Этот файл
```

## 🚀 Запуск тестов

### Локальный запуск

```bash
# Все тесты (без интеграционных, если нет API key)
pytest

# Конкретный тест
pytest tests/test_webhook_handler.py::TestWebhookHandler::test_should_process_pr_event_opened

# С подробным выводом
pytest -v -s

# Только unit тесты (без LLM интеграции)
pytest tests/test_webhook_handler.py

# С покрытием кода
pytest --cov=src --cov-report=html
```

### Интеграционные тесты с LLM

```bash
# Требуют LLM_API_KEY в .env
pytest tests/test_llm_integration.py -v -s
```

### CI/CD

Тесты автоматически запускаются в GitHub Actions при:
- Push в master
- Pull Request
- Ручном запуске (workflow_dispatch)

## 📋 Переменные окружения

### Для unit тестов
Не требуются - используются моки.

### Для интеграционных тестов

Создайте `.env` файл:
```env
LLM_API_KEY=your-api-key
LLM_API_BASE_URL=https://openrouter.ai/api/v1
LLM_MODEL=eliza-Internal-DeepSeek-V3-1-Terminus
```

### GitHub Actions

Добавьте секреты в GitHub:
- Settings → Secrets and variables → Actions
- Добавьте `LLM_API_KEY`

## 🧪 Текущие тесты

### test_webhook_handler.py - Unit тесты обработчика webhook

**Быстрые тесты без внешних зависимостей!**

- `test_should_process_pr_event_opened` - Обработка открытого PR
- `test_should_process_pr_event_synchronized` - Обработка обновления PR
- `test_should_not_process_closed_pr` - Пропуск закрытого PR
- `test_should_not_process_draft_pr` - Пропуск draft PR
- `test_extract_pr_info` - Извлечение информации о PR
- `test_is_comment_event` - Определение комментария
- `test_is_pr_comment` - Определение комментария в PR
- `test_extract_commands_from_comment` - Извлечение команд из комментария
- `test_should_process_comment_command` - Обработка команды @MergeBlocker review
- `test_extract_pr_info_from_comment` - Извлечение информации из комментария

Запуск:
```bash
pytest tests/test_webhook_handler.py -v
```

### test_llm_integration.py - Интеграционные тесты LLM

**Требуют LLM_API_KEY и реальные API запросы!**

- `test_llm_client_creation` - Создание LLM клиента
- `test_simple_generation` - Простая генерация текста
- `test_code_review_generation` - Генерация code review
- `test_small_pr_analysis` - Анализ небольшого PR

Запуск:
```bash
pytest tests/test_llm_integration.py -v -s
```

## 💡 Советы

### Пропуск LLM тестов

Тесты автоматически пропускаются если `LLM_API_KEY` не настроен:

```python
@pytest.fixture(scope="session")
def check_env_vars():
    if not os.getenv("LLM_API_KEY"):
        pytest.skip("LLM_API_KEY не настроен")
```

Это нормальное поведение - LLM тесты опциональны.

### Добавление новых тестов

1. Создайте файл `test_*.py` в папке `tests/`
2. Используйте fixtures из `conftest.py`
3. Для unit тестов используйте моки из fixtures
4. Для интеграционных тестов добавьте `check_env_vars` fixture

Пример unit теста с моком:

```python
def test_my_feature(mock_github_client):
    # mock_github_client автоматически мокирует GitHub API
    result = my_function(mock_github_client)
    assert result == expected
```

Пример интеграционного теста:

```python
def test_real_llm(check_env_vars, llm_client):
    # check_env_vars пропустит тест если API key отсутствует
    result = llm_client.generate("test prompt")
    assert result is not None
```

## 🐛 Troubleshooting

### Тесты падают с ImportError

Убедитесь что установлены зависимости:

```bash
pip install -r requirements.txt
```

### LLM тесты медленные

LLM интеграционные тесты требуют реальных API запросов:
- `test_simple_generation` - ~2-5 сек
- `test_code_review_generation` - ~5-10 сек
- `test_small_pr_analysis` - ~10-20 сек

Используйте `-k` для запуска только быстрых unit тестов:

```bash
pytest -k "not integration"
```

### Моки не работают как ожидается

Проверьте что используете правильные fixtures из `conftest.py`:
- `mock_github_client` - для GitHub API
- `mock_code_analyzer` - для code analyzer
- `sample_pr_event` - для PR события
- `sample_comment_event` - для комментария

## 📊 Coverage

Для проверки покрытия кода тестами:

```bash
pytest --cov=src --cov-report=term --cov-report=html
```

Откройте `htmlcov/index.html` в браузере для детального отчета.

---

**Обновлено:** 2024-12-14

