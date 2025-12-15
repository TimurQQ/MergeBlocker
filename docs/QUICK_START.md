# ⚡ Быстрый старт MergeBlocker (5 минут)

Минимальная инструкция для быстрого запуска.

## 1. Установка (1 минута)

```bash
cd /path/to/merge-bloker
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Конфигурация (2 минуты)

### Создайте .env файл:

```bash
cp .env.example .env
nano .env  # или любой редактор
```

### Заполните обязательные поля:

```env
GITHUB_APP_ID=2469635
GITHUB_PRIVATE_KEY_PATH=./private-key.pem
GITHUB_WEBHOOK_SECRET=<генерируйте: openssl rand -hex 32>
ANTHROPIC_API_KEY=<ваш Claude API key>
```

### Скачайте private key:

1. Откройте: https://github.com/settings/apps/mergeblocker
2. General → Private keys → Generate a private key
3. Сохраните как `private-key.pem` в корень проекта

## 3. Запуск (30 секунд)

```bash
python app.py
```

Вы увидите:
```
INFO - Starting MergeBlocker on 0.0.0.0:8000
```

## 4. Публичный endpoint (1 минута)

### Установите ngrok:

```bash
# macOS
brew install ngrok

# или скачайте: https://ngrok.com/download
```

### Запустите ngrok (в новом терминале):

```bash
ngrok http 8000
```

Скопируйте URL (например: `https://abc123.ngrok.io`)

## 5. Настройте Webhook (30 секунд)

1. Откройте: https://github.com/settings/apps/mergeblocker
2. General → Webhook
3. **Webhook URL**: `https://abc123.ngrok.io/webhook`
4. **Secret**: <тот же что в .env>
5. **Active**: ✅
6. Save changes

## 6. Установите App (30 секунд)

1. Откройте: https://github.com/settings/apps/mergeblocker/installations
2. Install → выберите репозиторий
3. Install

## 7. Тест (1 минута)

Создайте PR в установленном репозитории:

```bash
git checkout -b test-ai-review
echo "# Test" >> README.md
git add . && git commit -m "test: AI review"
git push origin test-ai-review
```

Создайте PR на GitHub → через 30-60 секунд увидите AI review! 🎉

---

## Что-то не работает?

**Webhook не приходит:**
```bash
# Проверьте логи сервера
# Проверьте ngrok: http://127.0.0.1:4040
```

**Invalid signature:**
```bash
# Проверьте GITHUB_WEBHOOK_SECRET в .env
# Убедитесь что он совпадает с GitHub App
```

**Private key error:**
```bash
# Проверьте что файл private-key.pem существует
ls -la private-key.pem
```

**Claude API error:**
```bash
# Проверьте ANTHROPIC_API_KEY
# Проверьте баланс: https://console.anthropic.com/
```

---

## Полная документация

- [README.md](./README.md) - Полная документация
- [SETUP_GUIDE.md](./SETUP_GUIDE.md) - Детальная инструкция
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Архитектура системы

---

**Готово за 5 минут!** 🚀
