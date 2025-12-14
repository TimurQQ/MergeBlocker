# 🤖 MergeBlocker - AI Code Review GitHub App

Автоматический code review для GitHub Pull Requests с использованием Claude AI.

## 🎯 Возможности

- ✅ **Автоматический анализ кода** при создании/обновлении PR
- 🎯 **Ручной review** по команде `@MergeBlocker review` в комментарии
- 📋 **Читает AGENTS.md** из репозитория для учета project guidelines
- 💬 **Inline комментарии** к конкретным строкам кода (без ограничений по количеству)
- 📝 **Структурированные reviews** с summary, критическими проблемами и рекомендациями
- 🔄 **JSON формат** с автоматическими retry при ошибках парсинга
- ⚡ **Быстрые проверки**: поиск секретов, TODO, размер PR
- 🎨 **Красивые GitHub Check Runs** для визуального статуса
- 🧠 **Детальный анализ**: всегда генерирует inline комментарии к коду
- 🔒 **Безопасность**: проверка webhook signature (HMAC SHA-256)
- 🧪 **Автотесты**: unit и integration тесты с pytest
- 🚀 **CI/CD**: автоматический lint, test, build и deploy через GitHub Actions

## 📋 Требования

- Python 3.11+
- Poetry (для dependency management) или pip
- GitHub App с правами:
  - Pull requests: Read & Write (reviews и inline comments)
  - Issues: Read & Write (чтение команд в комментариях)
  - Contents: Read-only (чтение AGENTS.md и файлов)
  - Checks: Read & Write (статусы Check Runs)
  - Metadata: Read-only (автоматически)
- LLM API key (OpenRouter-compatible API):
  - Model: `eliza-Internal-DeepSeek-V3-1-Terminus`
  - Same setup as ML-API project

## 🚀 Быстрый старт

### 1. Клонируйте репозиторий

```bash
cd /path/to/merge-bloker
```

### 2. Установите зависимости

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Настройте GitHub App

#### 3.1. Перейдите в настройки GitHub App

Ваше приложение: https://github.com/settings/apps/mergeblocker

#### 3.2. Настройте Permissions

В разделе **Permissions & events**:

- **Repository permissions:**
  - Pull requests: `Read & write` (для создания reviews и inline comments)
  - Issues: `Read & write` (для чтения команд `@MergeBlocker review`)
  - Contents: `Read-only` (для чтения `AGENTS.md` и файлов PR)
  - Checks: `Read & write` (для Check Runs статусов)
  - Commit statuses: `Read & write` (опционально)
  - Metadata: `Read-only` (автоматически)

#### 3.3. Настройте Events (Webhooks)

В разделе **Subscribe to events**:

- ✅ **Pull request** (для автоматического review)
- ✅ **Issue comment** (для команды `@MergeBlocker review`)
- ⚪ Pull request review (опционально, не используется)

#### 3.4. Получите Private Key

1. Прокрутите до раздела **Private keys**
2. Нажмите **Generate a private key**
3. Скачайте `.pem` файл
4. Переместите его в корень проекта: `private-key.pem`

**⚠️ ВАЖНО:** Не добавляйте `private-key.pem` в git!

#### 3.5. Настройте Webhook

В разделе **General → Webhook**:

1. **Webhook URL**: `https://your-domain.com/webhook`
   - Для разработки используйте ngrok или smee.io (см. ниже)
2. **Secret**: сгенерируйте случайный секрет (например: `openssl rand -hex 32`)
3. **Active**: ✅ включите

### 4. Настройте environment variables

Скопируйте `.env.example` в `.env`:

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
GITHUB_APP_ID=2469635
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret_here

ANTHROPIC_API_KEY=your_anthropic_api_key_here

PORT=8000
HOST=0.0.0.0
DEBUG=False
```

### 5. Установите App в репозиторий

1. Перейдите: https://github.com/settings/apps/mergeblocker/installations
2. Нажмите **Install** или **Configure**
3. Выберите репозитории (или все)

### 6. Запустите сервер

```bash
python app.py
```

Сервер запустится на `http://0.0.0.0:8002`

## 🌐 Настройка публичного endpoint (для разработки)

GitHub требует публичный HTTPS endpoint для webhooks. Варианты:

### Вариант 1: ngrok (рекомендуется)

```bash
# Установите ngrok: https://ngrok.com/download
ngrok http 8002
```

Вы получите URL типа `https://abc123.ngrok.io`

Укажите в GitHub App Webhook URL: `https://abc123.ngrok.io/webhook`

### Вариант 2: smee.io

```bash
npm install -g smee-client

# Создайте channel на https://smee.io
smee --url https://smee.io/abc123 --path /webhook --port 8002
```

Укажите в GitHub App Webhook URL: `https://smee.io/abc123`

## 📖 Использование

### Автоматический review

1. Создайте или обновите Pull Request
2. GitHub отправит webhook (`pull_request` event)
3. Приложение автоматически:
   - Читает `AGENTS.md` (если есть в репозитории)
   - Проанализирует изменения
   - Запустит AI review с учетом project guidelines
   - Оставит summary comment в Conversation
   - Добавит inline комментарии в Files Changed (до 10 штук)
   - Обновит Check Run статус

### Ручной review

Напишите комментарий в PR:

```
@MergeBlocker review
```

Бот автоматически:
- Получит webhook (`issue_comment` event)
- Запустит полный анализ PR
- Оставит review с учетом `AGENTS.md`

**Когда использовать:**
- ✅ Для повторного анализа после изменений
- ✅ Если автоматический review не сработал
- ✅ Для запуска review в старом PR

## ⚙️ Конфигурация

Настройки в `.env`:

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `SKIP_DRAFT_PRS` | Пропускать draft PR | True |

## 🏗️ Архитектура и процесс работы

### Общий процесс

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        GitHub Pull Request                               │
│                                                                           │
│  1. PR создан/обновлен   OR   2. Комментарий "@MergeBlocker review"    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ Webhook (POST /webhook)
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Flask Server (app.py)                           │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ 1. Verify webhook signature (HMAC SHA-256)                     │    │
│  │ 2. Parse event (pull_request или issue_comment)               │    │
│  │ 3. Check event type (opened/synchronized или command)          │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │ process_pr_review(pr_info)
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    Step 1: Create Check Run                              │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ GitHub Client → create_check_run()                              │    │
│  │ Status: "in_progress" ⏳                                        │    │
│  │ Title: "Analyzing code changes..."                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                Step 2: Fetch PR Context                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ GitHub Client → get_pr_context()                                │    │
│  │ • PR metadata (title, body, author, labels)                    │    │
│  │ • Changed files (filename, status, additions, deletions)       │    │
│  │ • Patches (diffs for each file)                                │    │
│  │ • Commits (last 5 for context)                                 │    │
│  │ • Statistics (total files, lines changed)                      │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            Step 2.5: Read AGENTS.md (if exists) 📋                      │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ GitHub Client → get_file_content("AGENTS.md")                   │    │
│  │ • Читает guidelines из репозитория                             │    │
│  │ • Используется в промптах для LLM                              │    │
│  │ • Позволяет учитывать правила проекта                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Step 3: Quick Deterministic Checks ⚡                       │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Code Analyzer → quick_check()                                   │    │
│  │ • Поиск потенциальных секретов (api_key, password, token)     │    │
│  │ • Поиск TODO/FIXME комментариев                                │    │
│  │ • Проверка размера PR                                          │    │
│  │ • Immediate warnings (без LLM)                                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                  Step 4: AI Analysis 🧠                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Code Analyzer → analyze_pr(pr_context, agents_md_content)      │    │
│  │                                                                 │    │
│  │ Всегда делается детальный анализ:                              │    │
│  │ • Полный анализ всех изменений (без ограничений)              │    │
│  │ • Inline комментарии к конкретным строкам (без ограничений)   │    │
│  │ • Структурированный JSON: summary, critical_issues,            │    │
│  │   suggestions, inline_comments                                 │    │
│  │ • Автоматический retry при невалидном JSON (до 3 попыток)     │    │
│  │                                                                 │    │
│  │ LLM Client (OpenRouter API):                                   │    │
│  │ • Model: eliza-Internal-DeepSeek-V3-1-Terminus                 │    │
│  │ • System Prompt: Expert code reviewer роль                     │    │
│  │ • User Prompt: PR context + AGENTS.md + changed files          │    │
│  │                                                                 │    │
│  │ Анализирует:                                                   │    │
│  │ • Security issues (secrets, vulnerabilities)                   │    │
│  │ • Potential bugs and edge cases                                │    │
│  │ • Code quality and maintainability                             │    │
│  │ • Performance concerns                                         │    │
│  │ • Best practices for language/framework                        │    │
│  │ • Testing coverage                                             │    │
│  │ • Соответствие AGENTS.md guidelines                            │    │
│  │                                                                 │    │
│  │ Возвращает:                                                    │    │
│  │ {                                                              │    │
│  │   "summary": "Overview + Critical Issues + Suggestions",      │    │
│  │   "inline_comments": [                                        │    │
│  │     {"path": "file.py", "line": 42, "body": "comment"},      │    │
│  │     ...                                                       │    │
│  │   ]                                                           │    │
│  │ }                                                             │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                Step 5: Format Review 📝                                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ Review Formatter → format_review_comment()                      │    │
│  │                                                                 │    │
│  │ Создает красивый markdown comment:                             │    │
│  │ • Header с emoji и metadata                                    │    │
│  │ • Quick warnings (если есть)                                   │    │
│  │ • AI review summary                                            │    │
│  │ • Inline comments notice                                       │    │
│  │ • Footer с disclaimer                                          │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│             Step 6: Post Review with Inline Comments 💬                  │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ GitHub Client → create_review()                                 │    │
│  │                                                                 │    │
│  │ body: formatted review summary                                 │    │
│  │ comments: [                                                    │    │
│  │   {                                                            │    │
│  │     path: "src/api.py",                                       │    │
│  │     line: 42,                                                 │    │
│  │     body: "🐛 Potential bug: ..."                             │    │
│  │   },                                                          │    │
│  │   ...                                                         │    │
│  │ ]                                                             │    │
│  │ event: "COMMENT"                                              │    │
│  │                                                               │    │
│  │ Результат в GitHub:                                           │    │
│  │ ✅ Summary comment в Conversation                            │    │
│  │ ✅ Inline comments в Files Changed                           │    │
│  └────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Step 7: Update Check Run ✅                                 │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │ GitHub Client → create_check_run()                              │    │
│  │ Status: "completed"                                            │    │
│  │ Conclusion: "success"                                          │    │
│  │ Title: "✅ Review Completed"                                   │    │
│  │ Summary: Statistics + warnings                                 │    │
│  └────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘

```

### Триггеры для code review

1. **Автоматический** (pull_request event):
   - PR открыт (`opened`)
   - PR обновлен (`synchronize`)
   - Пропускаются: `closed`, draft PR (если `SKIP_DRAFT_PRS=True`)

2. **Ручной** (issue_comment event):
   - Комментарий `@MergeBlocker review` в PR
   - Запускает полный анализ независимо от предыдущих reviews

## 📁 Структура проекта

```
merge-bloker/
├── app.py                      # Главный Flask сервер (точка входа)
├── requirements.txt            # Python зависимости (pip)
├── pyproject.toml              # Poetry конфигурация и метаданные
├── poetry.lock                 # Locked версии зависимостей
├── .env                        # Environment variables (создайте из .env.example)
├── .env.example                # Пример конфигурации
├── .gitignore                  # Git ignore
├── private-key.pem             # GitHub App private key (не в git!)
│
├── src/                        # Исходный код приложения
│   ├── config.py               # Конфигурация и environment variables
│   │
│   ├── clients/                # Клиенты для внешних API
│   │   ├── github_client.py    # GitHub API (PyGithub)
│   │   └── llm_client.py       # LLM API (OpenRouter-compatible)
│   │
│   ├── analysis/               # Анализ кода и форматирование
│   │   ├── code_analyzer.py    # Главная логика анализа
│   │   ├── prompts.py          # LLM промпты для review
│   │   └── review_formatter.py # Форматирование результатов
│   │
│   └── handlers/               # Обработчики событий
│       └── webhook_handler.py  # Парсинг и валидация webhooks
│
├── tests/                      # Тесты
│   ├── conftest.py             # Pytest fixtures
│   ├── test_webhook_handler.py # Unit тесты WebhookHandler
│   ├── test_llm_integration.py # Integration тесты LLM
│   └── README.md               # Документация по тестам
│
├── .github/                    # GitHub Actions CI/CD
│   └── workflows/
│       ├── deploy.yaml         # Build & Deploy workflow
│       └── test.yaml           # Lint & Test workflow
│
├── Dockerfile                  # Docker образ для production
├── docker-compose.yaml         # Docker Compose для разработки
├── docker-compose.prod.yaml    # Docker Compose для production
├── .dockerignore               # Игнорируемые файлы для Docker
│
├── deploy.sh                   # Скрипт деплоя на сервер
├── generate-env.sh             # Генерация .env из переменных окружения
├── start-local.sh              # Скрипт для локального запуска
│
├── .flake8                     # Конфигурация flake8 linter
├── README.md                   # Основная документация (вы здесь!)
│
└── docs/                       # Дополнительная документация
    ├── DEPLOYMENT.md           # CI/CD и деплой
    ├── SETUP_GUIDE.md          # Детальная инструкция по настройке
    ├── QUICK_START.md          # Быстрый старт (5 минут)
    ├── ARCHITECTURE.md         # Архитектура системы
    ├── PROJECT_SUMMARY.md      # Сводка проекта
    └── NEXT_STEPS.md           # Следующие шаги после установки
```

## 🔧 Разработка

### Логирование

Логи выводятся в stdout. Уровень логирования: `INFO`.

Для debug режима установите в `.env`:

```env
DEBUG=True
```

### Тестирование webhook

Отправьте тестовый webhook из GitHub:

1. Перейдите: Settings → Apps → MergeBlocker → Advanced
2. Найдите раздел "Recent Deliveries"
3. Нажмите "Redeliver" на любом событии

### Проверка работы

1. Создайте тестовый PR в репозитории
2. Проверьте логи сервера
3. Через ~30-60 секунд должен появиться комментарий

## 🚀 Production Deployment

### Автоматический CI/CD (рекомендуется)

Проект настроен для автоматического деплоя через GitHub Actions:

1. **Push в master** → автоматически:
   - Собирается Docker образ
   - Пушится в GitHub Container Registry
   - Деплоится на сервер через SSH

2. **Настройка**: см. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Docker Compose (локально или на сервере)

```bash
# Development
docker compose up

# Production
docker compose -f docker-compose.prod.yaml up -d
```

### Ручной деплой на сервер

```bash
# На сервере
git clone git@github.com:TimurQQ/MergeBlocker.git
cd MergeBlocker

# Настройте .env и private-key.pem
cp .env.example .env
# Отредактируйте .env

# Запустите деплой
./deploy.sh
```

### Рекомендации для production

1. **CI/CD**: Используйте GitHub Actions (уже настроено)
2. **Мониторинг**: Sentry для ошибок, Prometheus для метрик
3. **Reverse Proxy**: Nginx с SSL/TLS
4. **Task Queue**: Celery + Redis для асинхронной обработки
5. **База данных**: PostgreSQL для истории reviews
6. **Кэширование**: Redis для токенов и результатов

Подробнее: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## 🐛 Troubleshooting

### Webhook не приходит

1. Проверьте, что Webhook Active ✅
2. Проверьте Recent Deliveries в GitHub (Settings → Apps → Advanced)
3. Убедитесь, что endpoint доступен публично (попробуйте `curl https://your-url/`)
4. Проверьте логи сервера

### Ошибка "Invalid signature"

1. Проверьте `GITHUB_WEBHOOK_SECRET` в `.env`
2. Убедитесь, что secret совпадает с GitHub App

### Ошибка "Private key not found"

1. Убедитесь, что `private-key.pem` существует
2. Проверьте путь в `GITHUB_PRIVATE_KEY_PATH`

### Review не появляется

1. Проверьте логи сервера
2. Убедитесь, что PR не в draft (если `SKIP_DRAFT_PRS=True`)
3. Проверьте, что у App есть права Pull requests: Read & Write
4. Убедитесь, что App установлен в репозиторий

### Ошибка Claude API

1. Проверьте `ANTHROPIC_API_KEY`
2. Убедитесь, что у вас есть доступ к Claude API
3. Проверьте квоты и лимиты

## 📊 Логика работы

### Стратегия анализа

Для **всех PR** (независимо от размера):
- ✅ Полный детальный анализ всех изменений (без ограничений по количеству файлов)
- ✅ Inline комментарии к конкретным строкам кода (без ограничений по количеству)
- ✅ Структурированный JSON response с retry механизмом
- ✅ Summary (общая оценка PR)
- ✅ Critical Issues (критические проблемы безопасности/баги)
- ✅ Suggestions (рекомендации по улучшению)
- ✅ Учет guidelines из AGENTS.md (если есть в репозитории)

**Примечание**: 
- LLM возвращает структурированный JSON, при ошибках парсинга автоматически retry (до 3 попыток)

### Что проверяется

**Быстрые проверки:**
- Потенциальные секреты (api_key, password, etc.)
- TODO/FIXME в новом коде
- Размер PR

**AI анализ:**
- Security issues
- Потенциальные баги
- Edge cases
- Code quality
- Best practices
- Performance concerns
- Testing coverage

## 🤝 Contributing

Pull requests приветствуются! Для крупных изменений сначала откройте issue.

## 📝 License

MIT

## 🔗 Полезные ссылки

- [GitHub Apps Documentation](https://docs.github.com/en/apps)
- [PyGithub Documentation](https://pygithub.readthedocs.io/)
- [Anthropic Claude API](https://www.anthropic.com/api)
- [Flask Documentation](https://flask.palletsprojects.com/)

---

**Вопросы?** Создайте issue в репозитории!

