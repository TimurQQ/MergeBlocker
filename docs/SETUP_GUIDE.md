# 📖 Пошаговая инструкция по настройке MergeBlocker

## Шаг 1: Подготовка окружения

### 1.1. Убедитесь, что Python установлен

```bash
python --version  # Должна быть версия 3.9+
```

Если Python не установлен, скачайте с [python.org](https://www.python.org/downloads/)

### 1.2. Установите зависимости

```bash
cd /path/to/merge-bloker
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Шаг 2: Настройка GitHub App

### 2.1. Откройте настройки вашего GitHub App

URL: https://github.com/settings/apps/mergeblocker

### 2.2. Настройте Permissions (вкладка "Permissions & events")

Установите следующие права:

#### Repository permissions:
- ✅ **Pull requests**: `Read & write`
- ✅ **Contents**: `Read-only`
- ✅ **Checks**: `Read & write`
- ✅ **Commit statuses**: `Read & write`
- ✅ **Metadata**: `Read-only` (автоматически)

**Нажмите "Save changes" внизу страницы!**

### 2.3. Настройте Subscribe to events

В этой же вкладке прокрутите до "Subscribe to events":

- ✅ **Pull request**
- ✅ **Pull request review** (опционально)

**Нажмите "Save changes"!**

### 2.4. Сгенерируйте Private Key (вкладка "General")

1. Перейдите на вкладку **"General"**
2. Прокрутите до раздела **"Private keys"**
3. Нажмите **"Generate a private key"**
4. Скачается файл типа `mergeblocker.2024-12-14.private-key.pem`
5. **Переименуйте** его в `private-key.pem`
6. **Переместите** в корень проекта `/path/to/merge-bloker/private-key.pem`

⚠️ **ВАЖНО**: Не добавляйте этот файл в git! Он уже в `.gitignore`

### 2.5. Настройте Webhook (вкладка "General")

#### Если у вас уже есть публичный сервер:

1. В разделе **"Webhook"**:
   - **Webhook URL**: `https://your-domain.com/webhook`
   - **Secret**: сгенерируйте случайный секрет:
     ```bash
     openssl rand -hex 32
     ```
   - **Active**: ✅ включите галочку

#### Если вы на локальной машине (для разработки):

Пока **оставьте Webhook URL пустым**. Мы настроим его после запуска ngrok (см. Шаг 4).

**Нажмите "Save changes"!**

## Шаг 3: Получите Claude API Key

1. Зарегистрируйтесь на [Anthropic](https://www.anthropic.com/)
2. Перейдите в [Console](https://console.anthropic.com/)
3. Создайте API Key
4. Скопируйте ключ (начинается с `sk-ant-...`)

## Шаг 4: Настройте .env файл

### 4.1. Создайте .env из примера

```bash
cp .env.example .env
```

### 4.2. Откройте .env в редакторе

```bash
nano .env  # или используйте VS Code, Sublime, etc.
```

### 4.3. Заполните значения

```env
# GitHub App Configuration
GITHUB_APP_ID=2469635
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=ваш_секрет_из_шага_2.5  # Тот что сгенерировали с openssl

# LLM Configuration
ANTHROPIC_API_KEY=ваш_api_key_из_шага_3

# Server Configuration
PORT=8000
HOST=0.0.0.0
DEBUG=True  # Для разработки оставьте True

# Review Configuration
MAX_FILES_FOR_FULL_REVIEW=20
MAX_LINES_FOR_FULL_REVIEW=800
MAX_INLINE_COMMENTS=10
SKIP_DRAFT_PRS=True
```

**Сохраните файл!**

## Шаг 5: Запустите сервер

### Вариант A: Простой запуск

```bash
python app.py
```

Вы должны увидеть:

```
INFO - Configuration validated successfully
INFO - Starting MergeBlocker on 0.0.0.0:8000
* Running on http://0.0.0.0:8000
```

### Вариант B: Используя скрипт

```bash
chmod +x run_dev.sh
./run_dev.sh
```

## Шаг 6: Настройте публичный endpoint (для локальной разработки)

GitHub требует публичный HTTPS endpoint. Используем ngrok:

### 6.1. Установите ngrok

- Скачайте с [ngrok.com/download](https://ngrok.com/download)
- Или через brew: `brew install ngrok`

### 6.2. Зарегистрируйтесь и получите authtoken

```bash
ngrok config add-authtoken ваш_токен
```

### 6.3. Запустите ngrok

В **новом терминале** (сервер должен работать):

```bash
ngrok http 8000
```

Вы увидите:

```
Forwarding  https://abc123.ngrok.io -> http://localhost:8000
```

### 6.4. Скопируйте URL и обновите GitHub Webhook

1. Скопируйте URL типа `https://abc123.ngrok.io`
2. Вернитесь в GitHub App → General → Webhook
3. **Webhook URL**: `https://abc123.ngrok.io/webhook`
4. Если не создали Secret - создайте:
   ```bash
   openssl rand -hex 32
   ```
   И добавьте в `.env` как `GITHUB_WEBHOOK_SECRET`
5. **Active**: ✅
6. **Нажмите "Update webhook"** или "Save changes"

## Шаг 7: Установите App в репозиторий

### 7.1. Перейдите в Installations

URL: https://github.com/settings/apps/mergeblocker/installations

### 7.2. Установите приложение

1. Нажмите **"Install"** или **"Configure"**
2. Выберите:
   - **All repositories** (для тестирования можно выбрать один)
   - Или **Only select repositories** → выберите тестовый репозиторий
3. Нажмите **"Install"** или **"Save"**

## Шаг 8: Проверка работы

### 8.1. Создайте тестовый PR

1. В установленном репозитории создайте ветку:
   ```bash
   git checkout -b test-mergeblocker
   ```
2. Сделайте изменение:
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: Testing MergeBlocker"
   git push origin test-mergeblocker
   ```
3. Создайте Pull Request на GitHub

### 8.2. Проверьте логи сервера

Вы должны увидеть:

```
INFO - Received pull_request event with action: opened
INFO - Processing PR #123 in owner/repo (SHA: abc1234)
INFO - Fetching PR context for #123
INFO - Running quick checks for PR #123
INFO - Running AI analysis for PR #123
INFO - Posting review for PR #123 (2 inline comments)
INFO - Successfully completed review for PR #123
```

### 8.3. Проверьте PR на GitHub

Через 30-60 секунд вы должны увидеть:

- ✅ Check Run: "AI Code Review - ✅ Review Complete"
- 💬 Комментарий от вашего бота с review
- 💬 Inline комментарии (если есть)

## 🎉 Готово!

Ваш MergeBlocker работает!

## ❓ Что-то не работает?

### Проблема: Webhook не приходит

**Проверьте:**

1. Сервер запущен: `curl http://localhost:8000/`
2. ngrok работает: откройте `http://127.0.0.1:4040` для веб-интерфейса ngrok
3. Webhook URL правильный в GitHub App
4. Webhook Active ✅

**GitHub webhook deliveries:**

1. Settings → Apps → MergeBlocker → Advanced
2. Recent Deliveries → посмотрите статусы
3. Если 400/500 ошибка - нажмите на delivery → посмотрите Response

### Проблема: "Invalid signature"

**Решение:**

1. Проверьте `GITHUB_WEBHOOK_SECRET` в `.env`
2. Он должен совпадать с Secret в GitHub App → General → Webhook
3. Перезапустите сервер после изменения `.env`

### Проблема: "Private key not found"

**Решение:**

1. Убедитесь, что файл `private-key.pem` в корне проекта
2. Проверьте путь в `.env`: `GITHUB_PRIVATE_KEY_PATH=./private-key.pem`

### Проблема: Review не появляется

**Проверьте логи сервера на ошибки:**

```bash
# Запустите с DEBUG=True в .env
```

**Возможные причины:**

1. PR в draft состоянии (если `SKIP_DRAFT_PRS=True`)
2. Нет прав на репозиторий (проверьте Permissions)
3. Ошибка Claude API (проверьте `ANTHROPIC_API_KEY`)

### Проблема: Claude API error

**Решение:**

1. Проверьте API key: https://console.anthropic.com/
2. Убедитесь, что у вас есть кредиты
3. Проверьте квоты rate limit

## 📚 Дополнительные ресурсы

- [Основной README](./README.md) - полная документация
- [GitHub Apps Docs](https://docs.github.com/en/apps)
- [ngrok Docs](https://ngrok.com/docs)
- [Claude API Docs](https://docs.anthropic.com/)

## 💡 Советы для production

Когда будете готовы к продакшену:

1. **Deploy на облако**: Heroku, AWS, GCP, DigitalOcean
2. **Используйте настоящий домен** вместо ngrok
3. **Добавьте queue** (Celery + Redis) для асинхронной обработки
4. **Настройте мониторинг**: Sentry для ошибок
5. **Включите CI/CD**: автоматический деплой при push
6. **Добавьте БД**: PostgreSQL для хранения истории

---

**Успехов! 🚀**

