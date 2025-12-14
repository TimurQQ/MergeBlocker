# 🤖 MergeBlocker - AI Code Review GitHub App

Автоматический code review для GitHub Pull Requests с использованием Claude AI.

## 🎯 Возможности

- ✅ **Автоматический анализ кода** при создании/обновлении PR
- 💬 **Inline комментарии** к конкретным строкам кода
- 📝 **Детальные summary** с рекомендациями
- ⚡ **Быстрые проверки**: поиск секретов, TODO, больших PR
- 🎨 **Красивые GitHub Check Runs** для визуального статуса
- 🧠 **Умная стратегия**: детальный анализ для маленьких PR, summary для больших
- 🔒 **Безопасность**: проверка webhook signature

## 📋 Требования

- Python 3.9+
- GitHub App с правами:
  - Pull requests: Read & Write
  - Contents: Read
  - Checks: Read & Write
  - Metadata: Read
- LLM API key (OpenRouter-compatible API, same as ML-API)

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
  - Pull requests: `Read & write`
  - Contents: `Read-only`
  - Checks: `Read & write`
  - Commit statuses: `Read & write`
  - Metadata: `Read-only` (автоматически)

#### 3.3. Настройте Events (Webhooks)

В разделе **Subscribe to events**:

- ✅ Pull request
- ✅ Pull request review (опционально)

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
2. GitHub отправит webhook
3. Приложение автоматически:
   - Проанализирует изменения
   - Запустит AI review
   - Оставит комментарий с результатами
   - Добавит inline комментарии (если есть)
   - Обновит Check Run статус

### Ручной review (опционально)

Напишите комментарий в PR: `/review`

(Требуется реализация обработчика issue_comment events)

## ⚙️ Конфигурация

Настройки в `.env`:

| Параметр | Описание | По умолчанию |
|----------|----------|--------------|
| `MAX_FILES_FOR_FULL_REVIEW` | Макс. файлов для детального review | 20 |
| `MAX_LINES_FOR_FULL_REVIEW` | Макс. строк для детального review | 800 |
| `MAX_INLINE_COMMENTS` | Макс. inline комментариев | 10 |
| `SKIP_DRAFT_PRS` | Пропускать draft PR | True |

## 🏗️ Архитектура

```
┌─────────────────┐
│   GitHub Event  │
│   (PR opened)   │
└────────┬────────┘
         │
         │ webhook
         ▼
┌─────────────────────────┐
│   Flask Server          │
│   (webhook_handler.py)  │
└────────┬────────────────┘
         │
         │ verify + parse
         ▼
┌─────────────────────────┐
│   GitHub Client         │
│   (github_client.py)    │
│   - Fetch PR context    │
│   - Get files & diffs   │
└────────┬────────────────┘
         │
         │ PR context
         ▼
┌─────────────────────────┐
│   Code Analyzer         │
│   (code_analyzer.py)    │
│   - Quick checks        │
│   - AI analysis (Claude)│
└────────┬────────────────┘
         │
         │ review results
         ▼
┌─────────────────────────┐
│   Review Formatter      │
│   (review_formatter.py) │
│   - Format summary      │
│   - Format inline       │
└────────┬────────────────┘
         │
         │ formatted review
         ▼
┌─────────────────────────┐
│   GitHub Client         │
│   - Post review         │
│   - Update check run    │
└─────────────────────────┘
```

## 📁 Структура проекта

```
merge-bloker/
├── app.py                  # Главный Flask сервер
├── config.py               # Конфигурация
├── webhook_handler.py      # Обработка webhooks
├── github_client.py        # GitHub API client
├── code_analyzer.py        # AI анализ кода
├── review_formatter.py     # Форматирование результатов
├── requirements.txt        # Python зависимости
├── .env                    # Environment variables (создайте из .env.example)
├── .env.example            # Пример конфигурации
├── .gitignore              # Git ignore
├── private-key.pem         # GitHub App private key (не в git!)
├── Dockerfile              # Docker конфигурация
├── start-local.sh          # Скрипт для локального запуска
├── README.md               # Основная документация
└── docs/                   # Дополнительная документация
    ├── SETUP_GUIDE.md      # Детальная инструкция по настройке
    ├── QUICK_START.md      # Быстрый старт (5 минут)
    ├── ARCHITECTURE.md     # Архитектура системы
    ├── PROJECT_SUMMARY.md  # Сводка проекта
    └── NEXT_STEPS.md       # Следующие шаги после установки
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

**Small PR** (≤20 файлов, ≤800 строк):
- Полный анализ всех изменений
- До 10 inline комментариев
- Детальные рекомендации

**Large PR** (>20 файлов или >800 строк):
- High-level summary
- Топ рисков
- Рекомендация разбить на части

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

