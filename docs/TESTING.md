# Тестирование MergeBlocker

## 🚀 Быстрый запуск тестов

### Все тесты параллельно (быстро)
```bash
# Использует все доступные CPU cores
poetry run pytest -n auto

# Время выполнения: ~10-15 секунд (вместо 40)
```

### Только юнит-тесты (очень быстро)
```bash
# Пропускает интеграционные тесты с LLM
poetry run pytest -m "not integration"

# Время выполнения: ~2-3 секунды
```

### С coverage (для CI)
```bash
poetry run pytest -n auto --cov=src --cov-report=term --cov-report=xml
```

## 📊 Типы тестов

### Unit тесты (без внешних зависимостей)
- `tests/test_webhook_handler.py` - тесты WebhookHandler
- `tests/test_retry_logic.py` - тесты retry механизмов

**Не требуют:**
- ✅ LLM API key
- ✅ GitHub API key
- ✅ Интернет соединение

**Время выполнения:** ~2-3 секунды

### Integration тесты (требуют LLM API)
- `tests/test_llm_integration.py` - тесты с реальными LLM запросами

**Требуют:**
- ⚠️ LLM_API_KEY
- ⚠️ LLM_API_BASE_URL
- ⚠️ LLM_MODEL

**Время выполнения:** ~30-35 секунд (делают реальные API вызовы)

## 🎯 Команды для разных сценариев

### Локальная разработка (быстро)
```bash
# Только юнит-тесты, параллельно
poetry run pytest -n auto -m "not integration"
```

### CI/CD (полное покрытие)
```bash
# Все тесты + coverage
poetry run pytest -n auto --cov=src --cov-report=term --cov-report=xml
```

### Отладка конкретного теста
```bash
# Один тест, с подробным выводом
poetry run pytest tests/test_webhook_handler.py::TestWebhookHandler::test_extract_pr_info -vv
```

### Посмотреть какие тесты самые медленные
```bash
poetry run pytest --durations=10
```

## 📦 pytest-xdist (параллелизм)

Установлен `pytest-xdist` для параллельного запуска тестов:

```bash
# Авто-определение количества CPU
pytest -n auto

# Указать конкретное количество процессов
pytest -n 4

# Без параллелизма (по умолчанию)
pytest
```

**Ускорение:** 2-4x в зависимости от количества cores

## 🏷️ Маркеры тестов

Определены в `pyproject.toml`:

```python
@pytest.mark.integration  # Требует LLM API, медленно
@pytest.mark.unit          # Быстрые юнит-тесты
```

**Использование:**
```bash
# Только integration тесты
pytest -m integration

# Всё кроме integration
pytest -m "not integration"

# Только unit
pytest -m unit
```

## ⚙️ Настройка переменных окружения

### Для unit тестов (минимум)
```bash
export GITHUB_APP_ID="12345"
export GITHUB_WEBHOOK_SECRET="test-secret"
export LLM_API_KEY="test-key"
```

### Для integration тестов (реальные значения)
```bash
export LLM_API_KEY="your-real-api-key"
export LLM_API_BASE_URL="https://your-api-url.com"
export LLM_MODEL="your-model-name"
```

## 🐛 Отладка

### Показать весь вывод (без захвата)
```bash
pytest -s
```

### Остановиться на первой ошибке
```bash
pytest -x
```

### Запустить только упавшие тесты из предыдущего запуска
```bash
pytest --lf
```

### Показать локальные переменные при ошибках
```bash
pytest -l
```

## 📈 Coverage

### Посмотреть coverage в терминале
```bash
pytest --cov=src --cov-report=term-missing
```

### Сгенерировать HTML отчет
```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Установить минимальный порог coverage
```bash
pytest --cov=src --cov-fail-under=80
```

## 🚀 Оптимизация скорости тестов

### 1. Параллелизм (pytest-xdist)
✅ Уже настроен

```bash
pytest -n auto  # Используй все CPU
```

### 2. Пропуск медленных тестов
✅ Уже настроен через маркеры

```bash
pytest -m "not integration"
```

### 3. Кэширование (встроено в pytest)
```bash
# Первый запуск: 15 секунд
pytest -n auto

# Повторный запуск (если ничего не изменилось): 2 секунды
pytest -n auto
```

### 4. Запуск только измененных тестов
```bash
# Тесты связанные с измененным кодом
pytest --testmon

# Требует установки: pip install pytest-testmon
```

## 📊 Benchmark

### Без оптимизации (baseline)
```
pytest                           # 40 секунд
```

### С параллелизмом
```
pytest -n auto                   # 15 секунд (2.6x faster)
```

### Без integration тестов
```
pytest -m "not integration"      # 2 секунды (20x faster!)
```

### Лучший вариант для локальной разработки
```
pytest -n auto -m "not integration"  # 1-2 секунды
```

## 🎯 Рекомендации

**Для локальной разработки:**
```bash
pytest -n auto -m "not integration" -v
```

**Перед коммитом:**
```bash
pytest -n auto --cov=src
```

**В CI/CD:**
```bash
pytest -n auto --cov=src --cov-report=xml
```
