# Исправление ошибки 401 Bad Credentials

## Проблема
```
401 {"message": "Bad credentials"}
```

## Что было сделано

✅ Добавлено детальное логирование в код
✅ Добавлена валидация webhook payload
✅ Созданы скрипты для диагностики

## Быстрый старт

### 1. Настройте секреты в GitHub (один раз)
`Settings → Secrets and variables → Actions`

Добавьте:
- `APP_ID`
- `WEBHOOK_SECRET`
- `PRIVATE_KEY_BASE64`

(См. [CI/CD интеграция](#cicd-интеграция) для деталей)

### 2. Закоммитьте изменения и запушьте

```bash
git add .
git commit -m "fix: Add diagnostic logging for 401 error"
git push origin master
```

**Всё остальное автоматически:**
1. ✅ GitHub Actions проверит credentials
2. ✅ Запустит тесты
3. ✅ Соберет Docker образ
4. ✅ Задеплоит на сервер

### 3. Тестирование
```bash
# Откройте PR и напишите комментарий
@MergeBlocker review

# На сервере смотрите логи
ssh deploy@your-server
docker compose -f docker-compose.prod.yaml logs -f mergeblocker
```

## Что искать в логах

### ✅ Правильно (найдется причина проблемы):
```
Extracted PR info - installation_id: 12345678, repo: owner/repo, PR: 123
Creating client for installation_id: 12345678
Using GitHub App ID: 123456
Private key length: 1675 chars
Successfully obtained access token for installation 12345678
```

### ❌ Проблема найдена:
```
WARNING: No installation in webhook payload
# ИЛИ
Error creating installation client: 401 Bad credentials
```

## Типичные проблемы и решения

### Проблема 1: `No installation in webhook payload`

**Причина:** Вебхук настроен как repository webhook вместо GitHub App webhook

**Решение:**
1. Удалите webhooks на уровне репозитория: `https://github.com/<owner>/<repo>/settings/hooks`
2. Проверьте что webhook есть в GitHub App: `https://github.com/settings/apps/<your-app-name>`
3. Убедитесь что App установлено: `https://github.com/settings/installations`

---

### Проблема 2: Неверный App ID

**Симптом:** Логи показывают `Using GitHub App ID: 999999` (неправильный)

**Решение:**
```bash
# На сервере проверьте .env
sudo cat /opt/mergeblocker/.env | grep GITHUB_APP_ID

# Сравните с реальным App ID: https://github.com/settings/apps/<your-app-name>
# Исправьте .env и перезапустите
sudo vim /opt/mergeblocker/.env
sudo docker-compose restart
```

---

### Проблема 3: Неверный приватный ключ

**Симптом:** Правильный App ID в логах, но все равно 401

**Решение:**
1. Сгенерируйте новый ключ: `https://github.com/settings/apps/<your-app-name>`
2. Скачайте `private-key.pem`
3. Замените на сервере:

```bash
# Скопируйте на сервер
scp private-key.pem user@phantasma-vm:/tmp/

# На сервере
sudo cp /tmp/private-key.pem /opt/mergeblocker/
sudo chown deploy:deploy /opt/mergeblocker/private-key.pem
sudo chmod 600 /opt/mergeblocker/private-key.pem
sudo rm /tmp/private-key.pem

# Перезапустите
cd /opt/mergeblocker
sudo docker-compose restart
```

---

### Проблема 4: App не установлено на репозитории

**Решение:**
1. Перейдите: `https://github.com/settings/installations`
2. Нажмите на ваше приложение
3. Убедитесь, что нужный репозиторий включен
4. Проверьте разрешения:
   - Contents: Read
   - Pull requests: Read & Write
   - Issues: Read & Write

---

## Автоматическая диагностика в CI

### src/scripts/validate_credentials.py
Скрипт автоматически запускается в GitHub Actions перед всеми тестами.

**Что проверяет:**
1. ✅ GitHub App ID (формат и значение)
2. ✅ Webhook secret (наличие)
3. ✅ Приватный ключ (существование, формат)
4. ✅ GitHub Integration (создание)
5. ✅ Access token генерация
6. ✅ Installations (наличие)

**Exit codes:**
- `0` - ✅ Все проверки пройдены
- `1` - ❌ Критическая ошибка → CI останавливается

**Workflow:**
```
push/PR → validate-credentials → lint/test/docker-test → build → deploy
             ↓ (если упало)
          ❌ STOP
```

**Использование только в CI/CD** - не предназначен для ручного запуска.

---

## Полезные команды

### Работа с контейнером
```bash
# Просмотр логов
docker-compose logs --tail=50 mergeblocker
docker-compose logs -f mergeblocker

# Проверка переменных окружения
docker exec $(docker-compose ps -q mergeblocker) printenv | grep GITHUB

# Проверка приватного ключа
docker exec $(docker-compose ps -q mergeblocker) test -r /app/private-key.pem && echo "✅ OK" || echo "❌ FAIL"
docker exec $(docker-compose ps -q mergeblocker) head -n 1 /app/private-key.pem

# Перезапуск
docker-compose restart

# Полная пересборка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## Что изменилось в коде

### src/clients/github_client.py
Метод `get_installation_client()`:
- Добавлено логирование installation_id
- Добавлено логирование GitHub App ID
- Добавлено логирование длины приватного ключа
- Добавлен try-catch с детальной обработкой ошибок

### src/handlers/webhook_handler.py
Методы `extract_pr_info()` и `extract_pr_info_from_comment()`:
- Добавлена проверка наличия объекта `installation` в payload
- Добавлены детальные сообщения об ошибках если installation отсутствует

### app.py
Функция `webhook()`:
- Добавлено логирование извлеченной информации о PR
- Вывод installation_id, repo_full_name, pr_number

---

## После успешного исправления

Вы увидите в логах:
```
INFO - Successfully completed review for PR #123
```

И review появится на вашем Pull Request! 🎉

---

## Проверка настроек GitHub App

### 1. App ID и Private Key
URL: `https://github.com/settings/apps/<your-app-name>`
- Проверьте App ID (число в верхней части)
- Сгенерируйте новый Private Key если нужно

### 2. Permissions
URL: `https://github.com/settings/apps/<your-app-name>/permissions`

Необходимы:
- Repository permissions > Contents: Read
- Repository permissions > Pull requests: Read & Write
- Repository permissions > Issues: Read & Write

### 3. Webhooks
URL: `https://github.com/settings/apps/<your-app-name>`

Проверьте:
- Webhook URL: `https://your-domain.com/webhook`
- Content type: `application/json`
- Secret: Должен совпадать с `GITHUB_WEBHOOK_SECRET` в `.env`
- Events: Pull request, Issue comment

### 4. Installations
URL: `https://github.com/settings/installations`

Убедитесь, что App установлено на нужном репозитории.

---

## CI/CD интеграция

**Валидация credentials автоматически запускается в GitHub Actions при каждом push/PR!**

### Настройка секретов

`Settings → Secrets and variables → Actions → New repository secret`

**Обязательные секреты для валидации:**
1. **`APP_ID`** - ID вашего GitHub App
2. **`WEBHOOK_SECRET`** - Webhook secret
3. **`PRIVATE_KEY_BASE64`** - Приватный ключ в base64

**Как создать PRIVATE_KEY_BASE64:**
```bash
cat private-key.pem | base64
# Или на Mac:
cat private-key.pem | base64 | pbcopy
```

⚠️ **Важно:** GitHub не разрешает секреты с префиксом `GITHUB_`!

### Как работает CI

При каждом push/PR автоматически:

1. **validate-credentials** ← Первым делом
   - Проверяет APP_ID, WEBHOOK_SECRET, PRIVATE_KEY_BASE64
   - Создает GitHub Integration
   - Генерирует access token
   - ❌ Если упала → CI останавливается

2. **lint, test, docker-test** ← Параллельно
   - Запускаются одновременно
   - Независимы друг от друга

**Результат:** Невозможно задеплоить с неправильными credentials!

### Автоматический деплой

При push в `master`:

```
GitHub Push
    ↓
validate-credentials (проверка)
    ↓
lint + test + docker-test (параллельно)
    ↓
build (Docker образ)
    ↓
push (GHCR)
    ↓
deploy (SSH на сервер)
    ├─ git pull (обновление кода)
    ├─ docker pull (новый образ)
    └─ deploy.sh (запуск)
```

**Ничего не нужно делать вручную!** Просто push в master.

---

## Структура файлов

```
merge-bloker/
├── README_401_FIX.md                ← Этот файл
├── .github/workflows/test.yaml      🔄 CI/CD с автоматической валидацией
├── app.py                           (изменен - добавлено логирование)
└── src/
    ├── scripts/
    │   └── validate_credentials.py  ✅ Единственный скрипт для диагностики
    ├── clients/
    │   └── github_client.py         (изменен - добавлено логирование)
    └── handlers/
        └── webhook_handler.py       (изменен - добавлена валидация)
```

**Это всё!** Минимум файлов, максимум пользы. 🚀
