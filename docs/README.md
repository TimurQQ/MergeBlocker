# 📚 MergeBlocker Documentation

Документация по архитектуре, обновлениям и troubleshooting.

## 📖 Содержание:

### 🚀 Обновления и миграции

- **[UPGRADE_CLAUDE.md](./UPGRADE_CLAUDE.md)** - Апгрейд на Claude 4.5 Sonnet с thinking mode
  - Thinking mode с budget_tokens
  - Fallback на Gemini 3 Pro для больших PR
  - Нативный Anthropic API

- **[QUART_MIGRATION.md](./QUART_MIGRATION.md)** - Переход с Flask на Quart (async)
  - Преимущества async архитектуры
  - Изменения в коде
  - Производительность

- **[TESTS_ASYNC_UPDATE.md](./TESTS_ASYNC_UPDATE.md)** - Обновление тестов для async
  - Миграция на pytest-asyncio
  - AsyncMock для тестирования
  - Примеры использования

### 🔧 Troubleshooting

- **[README_401_FIX.md](./README_401_FIX.md)** - Решение проблемы "401 Bad credentials"
  - Настройка GitHub App
  - Валидация креденшалов
  - CI/CD интеграция

## 🎯 Быстрый старт:

1. **Для разработчиков** → начните с [README.md](../README.md) в корне
2. **Для понимания async архитектуры** → [QUART_MIGRATION.md](./QUART_MIGRATION.md)
3. **Для настройки Claude** → [UPGRADE_CLAUDE.md](./UPGRADE_CLAUDE.md)
4. **При проблемах с GitHub** → [README_401_FIX.md](./README_401_FIX.md)

## 📊 Ключевые технологии:

- **Web Framework:** Quart (async Flask)
- **LLM:** Claude 4.5 Sonnet + Gemini 3 Pro (fallback)
- **HTTP Client:** httpx.AsyncClient
- **Server:** Hypercorn (ASGI)
- **Testing:** pytest-asyncio
- **CI/CD:** GitHub Actions
