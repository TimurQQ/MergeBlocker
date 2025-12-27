# Оптимизация Docker Build

## Внесённые изменения

### 1. Переход на Poetry в Docker
Dockerfile теперь использует Poetry вместо pip для установки зависимостей:

```dockerfile
# Install Poetry
ENV POETRY_VERSION=1.8.2 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install "poetry==$POETRY_VERSION"

# Install dependencies with Poetry
RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry install --only main --no-root --no-interaction --no-ansi
```

**Результат:**
- Консистентность зависимостей между dev и prod
- Детерминированные сборки через `poetry.lock`
- Правильное разрешение версий зависимостей

### 2. BuildKit Cache Mount для Poetry
Два уровня кэширования:
- `/root/.cache/pip` - для установки самого Poetry
- `/root/.cache/pypoetry` - для скачанных Python-пакетов

**Результат:** Скачанные пакеты кэшируются между сборками, что значительно ускоряет повторные сборки.

### 3. Docker Layer Caching в CI/CD
В `.github/workflows/deploy.yaml` добавлено кэширование слоёв Docker:

- `docker/setup-buildx-action@v3` - настройка BuildKit
- `cache-from: type=gha` - использование кэша из GitHub Actions
- `cache-to: type=gha,mode=max` - сохранение максимального кэша

**Результат:** Слои Docker кэшируются между запусками CI/CD.

## Ожидаемые улучшения

### Первая сборка (без кэша)
- Установка Poetry: ~2-3 секунды
- Установка зависимостей: ~8-10 секунд
- Кэш создаётся

### Повторные сборки (с кэшем)
- При изменении кода: `poetry install` пропускается полностью (~0.5s)
- При изменении `pyproject.toml`: только новые пакеты скачиваются (~2-4s)
- **Ускорение: до 80-90%** для типичных изменений кода

## Как это работает

1. **BuildKit cache mount для Poetry:**
   - Кэш Poetry хранится в `/root/.cache/pypoetry` внутри контейнера
   - Кэш pip (для установки Poetry) хранится в `/root/.cache/pip`
   - При повторных сборках кэши переиспользуются
   - Пакеты не скачиваются заново

2. **GitHub Actions cache:**
   - Docker слои сохраняются в GitHub Actions Cache
   - При следующем запуске CI слои восстанавливаются
   - Только изменённые слои пересобираются

3. **Poetry преимущества:**
   - `poetry.lock` гарантирует одинаковые версии в dev и prod
   - `--only main` устанавливает только production зависимости
   - `--no-root` не устанавливает сам проект (только зависимости)

## Мониторинг эффективности

Проверить эффективность кэширования можно в логах CI:

- `RUN poetry install ...` - должен показывать `CACHED` при повторных сборках
- Общее время сборки должно снизиться с ~15-20s до ~3-5s
- Первый запуск создаст кэш, последующие будут использовать его

## Дополнительные рекомендации

1. **Локальная разработка:** Используйте `DOCKER_BUILDKIT=1 docker build .` для включения BuildKit
2. **Очистка кэша:** `docker builder prune` для очистки кэша при необходимости
3. **Размер кэша:** GitHub Actions кэш имеет лимит 10 GB на репозиторий
