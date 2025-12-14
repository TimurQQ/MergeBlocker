# 📊 MergeBlocker - Сводка проекта

## 🎯 Что это?

**MergeBlocker** - GitHub App для автоматического code review с использованием Claude AI.

### Основные возможности:
- ✅ Автоматический анализ PR при создании/обновлении
- 💬 Inline комментарии к конкретным строкам кода
- 📝 Детальное summary с рекомендациями
- ⚡ Быстрые проверки (секреты, TODO, размер PR)
- 🎨 GitHub Check Runs для визуального статуса
- 🧠 Умная стратегия: детальный анализ для маленьких PR, summary для больших

## 📁 Структура проекта

```
merge-bloker/
├── app.py                    # 🚀 Главный Flask сервер
├── config.py                 # ⚙️ Управление конфигурацией
├── webhook_handler.py        # 📡 Обработка GitHub webhooks
├── github_client.py          # 🐙 GitHub API client
├── code_analyzer.py          # 🧠 AI анализ кода (Claude)
├── review_formatter.py       # 📝 Форматирование результатов
├── requirements.txt          # 📦 Python зависимости
├── .env.example              # 🔧 Пример конфигурации
├── .gitignore                # 🚫 Git ignore
├── start-local.sh            # 🏃 Скрипт для локального запуска
├── Dockerfile                # 🐳 Для Docker deployment
├── README.md                 # 📖 Основная документация
└── docs/                     # 📚 Дополнительная документация
    ├── SETUP_GUIDE.md        # Детальная инструкция по настройке
    ├── QUICK_START.md        # Быстрый старт (5 минут)
    ├── ARCHITECTURE.md       # Архитектура системы
    ├── PROJECT_SUMMARY.md    # Сводка проекта
    └── NEXT_STEPS.md         # Следующие шаги после установки
```

## 🔑 Ключевые компоненты

### 1. Flask Server (`app.py`)
- Принимает webhooks от GitHub
- Координирует процесс review
- Обрабатывает ошибки gracefully

### 2. Webhook Handler (`webhook_handler.py`)
- Верификация HMAC signature
- Парсинг GitHub events
- Фильтрация событий для обработки

### 3. GitHub Client (`github_client.py`)
- JWT аутентификация
- Получение PR контекста (files, diffs, commits)
- Создание reviews с inline комментариями
- Управление Check Runs

### 4. Code Analyzer (`code_analyzer.py`)
- Быстрые детерминированные проверки
- AI анализ через Claude API
- Умная стратегия для разных размеров PR
- Парсинг результатов в структурированный формат

### 5. Review Formatter (`review_formatter.py`)
- Форматирование markdown комментариев
- Inline комментарии с AI badge
- Check Run summaries
- Error messages

### 6. Config (`config.py`)
- Загрузка из .env
- Валидация параметров
- Типизированные настройки

## 🔄 Workflow

```
PR создан/обновлен
    ↓
GitHub отправляет webhook
    ↓
Flask получает и верифицирует
    ↓
Извлечение PR контекста (files, diffs)
    ↓
Быстрые проверки (секреты, TODO)
    ↓
AI анализ (Claude)
    ↓
Форматирование результатов
    ↓
Создание review + inline комментарии
    ↓
Обновление Check Run статуса
```

## 📊 Технический стек

### Backend
- **Python 3.9+**
- **Flask** - веб-сервер
- **PyGithub** - GitHub API client
- **PyJWT** - JWT аутентификация
- **Anthropic** - Claude AI API

### Deployment
- **Gunicorn** - WSGI сервер для production
- **Docker** - контейнеризация
- **Heroku** - облачный хостинг (опционально)

## 🚀 Как запустить?

### Quick Start (5 минут):
См. [QUICK_START.md](./QUICK_START.md)

### Детальная инструкция:
См. [SETUP_GUIDE.md](./SETUP_GUIDE.md)

### Краткая версия:

```bash
# 1. Установка
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Конфигурация
cp .env.example .env
# Отредактируйте .env с вашими ключами

# 3. Запуск
python app.py

# 4. Публичный endpoint (для dev)
ngrok http 8000

# 5. Настройте webhook в GitHub App
# URL: https://your-ngrok-url.ngrok.io/webhook

# 6. Установите App в репозиторий

# 7. Создайте PR и наслаждайтесь! 🎉
```

## 🔐 Безопасность

- ✅ HMAC SHA-256 для webhook signature
- ✅ JWT аутентификация для GitHub API
- ✅ Private key вне git (.gitignore)
- ✅ Environment variables для секретов
- ✅ Installation tokens с ограниченными правами

## ⚙️ Конфигурация

Основные настройки в `.env`:

| Параметр | Описание | Значение по умолчанию |
|----------|----------|-----------------------|
| `GITHUB_APP_ID` | ID вашего GitHub App | 2469635 |
| `GITHUB_PRIVATE_KEY_PATH` | Путь к private key | ./private-key.pem |
| `GITHUB_WEBHOOK_SECRET` | Секрет для webhooks | - |
| `ANTHROPIC_API_KEY` | Claude API key | - |
| `MAX_FILES_FOR_FULL_REVIEW` | Макс. файлов для детального review | 20 |
| `MAX_LINES_FOR_FULL_REVIEW` | Макс. строк для детального review | 800 |
| `MAX_INLINE_COMMENTS` | Макс. inline комментариев | 10 |
| `SKIP_DRAFT_PRS` | Пропускать draft PR | True |

## 📈 Что анализируется?

### Быстрые проверки:
- 🔐 Потенциальные секреты (API keys, passwords)
- 📝 TODO/FIXME в новом коде
- 📊 Размер PR

### AI анализ:
- 🔒 Security vulnerabilities
- 🐛 Potential bugs
- 🎯 Edge cases
- ✨ Code quality & maintainability
- 🚀 Performance concerns
- ✅ Best practices
- 🧪 Testing coverage

## 🎨 Примеры output

### Summary комментарий:
```markdown
# 🤖 AI Code Review

**PR:** #123 - Add user authentication
**Commit:** `abc1234`
**Reviewed at:** 2024-12-14 10:30 UTC

---

## ⚡ Quick Checks
- ⚠️ Potential secret detected in `config.py` (pattern: api_key)

---

## Summary
- New authentication system using JWT tokens
- Good separation of concerns with dedicated auth module
- Consider adding rate limiting for login attempts

## Critical Issues
- [None found]

## Suggestions
1. Add unit tests for AuthService
2. Consider using bcrypt instead of SHA-256 for password hashing
3. Add logging for failed login attempts
4. Implement account lockout after N failed attempts

---

## 💬 Inline Comments
I've left 3 inline comment(s) on specific lines of code.
Please check the "Files changed" tab to see them.

---

🤖 This review was generated by MergeBlocker AI.
```

### Inline комментарий:
```markdown
🤖 **AI Review**

Consider using a constant for the max retry count instead of hardcoding `3`.
This makes it easier to adjust in the future.

```python
MAX_RETRIES = 3
for i in range(MAX_RETRIES):
    ...
```
```

### Check Run:
```
✅ Review Complete (2 warning(s))

**PR:** #123 - Add user authentication
**Commit:** `abc1234`

**Warnings:** 2
**Inline Comments:** 3

✅ AI code review completed successfully.

Check the PR comments for detailed feedback.
```

## 📚 Документация

- [README.md](./README.md) - Полная документация
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Пошаговая настройка
- [QUICK_START.md](./QUICK_START.md) - Быстрый старт (5 минут)
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Архитектура и технические детали

## 🚀 Production Deployment

### Heroku (рекомендуется для начала)

```bash
heroku create mergeblocker
heroku config:set GITHUB_APP_ID=2469635
heroku config:set GITHUB_WEBHOOK_SECRET=...
heroku config:set ANTHROPIC_API_KEY=...
git push heroku main
```

### Docker

```bash
docker build -t mergeblocker .
docker run -p 8000:8000 --env-file .env mergeblocker
```

### AWS / GCP / Azure

См. [ARCHITECTURE.md](./ARCHITECTURE.md) - раздел "Deployment"

## 🔮 Будущие улучшения

### Приоритет 1 (MVP+):
- [ ] Асинхронная обработка (Celery + Redis)
- [ ] База данных для истории reviews
- [ ] Manual trigger через `/review` комментарий
- [ ] Retry logic для API calls

### Приоритет 2:
- [ ] Config файл в репозитории (`.github/mergeblocker.yml`)
- [ ] Кэширование (installation tokens, PR contexts)
- [ ] Мониторинг (Sentry, Prometheus)
- [ ] Unit & Integration tests

### Приоритет 3:
- [ ] Поддержка других LLM (GPT-4, Gemini)
- [ ] Code suggestions с автоматическими исправлениями
- [ ] Интеграции (Jira, Slack, Datadog)
- [ ] Learning mode через feedback

## 💡 Лучшие практики

### Development:
```bash
# Всегда используйте виртуальное окружение
python -m venv venv
source venv/bin/activate

# Запускайте с DEBUG=True
export DEBUG=True
python app.py

# Используйте ngrok для тестирования webhooks
ngrok http 8000
```

### Production:
```bash
# Используйте gunicorn
gunicorn app:app --workers 4

# Включите мониторинг
# Добавьте Sentry для ошибок

# Используйте task queue
# Celery + Redis для асинхронной обработки

# Настройте автоскейлинг
# Базируясь на длине очереди
```

## 🐛 Troubleshooting

### Проблема: Webhook не приходит
**Решение:**
- Проверьте Recent Deliveries в GitHub App
- Убедитесь что endpoint публичный (попробуйте curl)
- Проверьте логи сервера

### Проблема: Invalid signature
**Решение:**
- Проверьте `GITHUB_WEBHOOK_SECRET` в `.env`
- Убедитесь что он совпадает с GitHub App

### Проблема: Review не появляется
**Решение:**
- Проверьте логи на ошибки
- Убедитесь что PR не в draft
- Проверьте права (Pull requests: Read & Write)
- Проверьте Claude API key и баланс

## 📞 Поддержка

**Вопросы или проблемы?**
- Создайте issue в репозитории
- Проверьте [SETUP_GUIDE.md](./SETUP_GUIDE.md) - детальные инструкции
- Изучите [ARCHITECTURE.md](./ARCHITECTURE.md) - технические детали

## 📝 Лицензия

MIT License

---

**Версия:** 1.0.0  
**Дата:** 2024-12-14  
**Статус:** ✅ Готов к использованию

🚀 **Happy Reviewing!**

